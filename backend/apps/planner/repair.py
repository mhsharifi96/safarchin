"""Bounded repair loop for structured LLM output: if the model's response
doesn't validate against the target Pydantic schema, we feed the validation
error back and ask it to correct itself, up to `max_attempts` times."""
import logging

from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class RepairExhausted(RuntimeError):
    def __init__(self, attempts: int, last_error: Exception):
        super().__init__(f"Structured output still invalid after {attempts} attempts: {last_error}")
        self.attempts = attempts
        self.last_error = last_error


def run_with_structured_repair(
    chat_model,
    schema: type[BaseModel],
    messages: list[BaseMessage],
    *,
    max_attempts: int = 3,
):
    structured_model = chat_model.with_structured_output(schema, include_raw=True)
    working_messages = list(messages)
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        result = structured_model.invoke(working_messages)
        parsed = result.get("parsed") if isinstance(result, dict) else None
        parsing_error = result.get("parsing_error") if isinstance(result, dict) else None

        if parsed is not None and parsing_error is None:
            try:
                return schema.model_validate(parsed if isinstance(parsed, dict) else parsed.model_dump())
            except ValidationError as exc:
                last_error = exc
        else:
            last_error = parsing_error or ValueError("No structured output returned")

        logger.warning("Structured output repair attempt %s/%s failed: %s", attempt, max_attempts, last_error)
        raw_message = result.get("raw") if isinstance(result, dict) else None
        working_messages.append(raw_message if raw_message is not None else HumanMessage(content=""))
        working_messages.append(
            HumanMessage(
                content=(
                    "خروجی قبلی با اسکیمای موردنیاز مطابقت نداشت. خطا: "
                    f"{last_error}\nلطفاً فقط یک JSON معتبر مطابق اسکیما برگردان."
                )
            )
        )

    raise RepairExhausted(max_attempts, last_error or RuntimeError("unknown"))
