declare module "@neshan-maps-platform/leaflet" {
  import type * as Leaflet from "leaflet";

  interface NeshanMapOptions extends Leaflet.MapOptions {
    key: string;
    maptype?: "dreamy" | "standard-day" | "standard-night" | "standard-no-traffic";
  }

  const L: typeof Leaflet & {
    Map: new (element: string | HTMLElement, options: NeshanMapOptions) => Leaflet.Map;
  };
  export default L;
}
