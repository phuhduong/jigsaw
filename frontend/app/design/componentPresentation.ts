import type { Component } from "../services/api/designRunApi.ts";

export type ComponentRole =
  | "controller"
  | "sensor"
  | "power"
  | "connector"
  | "other";

function getDescriptionSubject(text: string): string {
  return text.split(
    /\b(?:for|to|with|from|providing|using|supplying|via)\b/i,
  )[0];
}

function getDescriptionRole(text: string): ComponentRole {
  const subject = getDescriptionSubject(text);
  if (
    /\b(?:regulator|converter|ldo|charger|power supply|power stage)\b|steps?[- ]down|^regulates?\b/i.test(
      subject,
    )
  )
    return "power";
  if (
    /\b(?:microcontroller|controller|processor|processing|mcu|cpu)\b|^controls? the (?:system|device)\b/i.test(
      subject,
    )
  )
    return "controller";
  if (
    /\b(?:sensor|sensing|measurement|accelerometer|gyroscope|thermometer)\b|^measures?\b[^,;.]*\b(?:temperature|humidity|light|motion|acceleration)\b/i.test(
      subject,
    )
  )
    return "sensor";
  return "other";
}

export function getComponentRole(part: Component): ComponentRole {
  if (part.kind === "connector") return "connector";
  if (part.kind === "passive") return "other";
  // A catalog's component type is less ambiguous than a purpose such as
  // "Monitors the tilt sensor", where the sensor is a different part.
  for (const text of [
    part.name,
    part.product?.description ?? "",
    part.purpose,
  ]) {
    const role = getDescriptionRole(text);
    if (role !== "other") return role;
  }
  return "other";
}

/** Short visual labels summarize recorded descriptions; they do not verify capability. */
export function getComponentTitle(part: Component): string {
  const descriptions = [
    part.purpose,
    part.name,
    part.product?.description ?? "",
  ];
  const text = descriptions.map(getDescriptionSubject).join(" ");
  switch (getComponentRole(part)) {
    case "connector":
      if (/\bbattery (?:holder|retainer)\b/i.test(text))
        return "Battery holder";
      if (/usb[- ]?(?:type[- ]?)?c\b/i.test(text))
        return /power|supply/i.test(getDescriptionSubject(part.purpose))
          ? "USB-C input"
          : "USB-C connector";
      return /power|supply/i.test(getDescriptionSubject(part.purpose))
        ? "Power connector"
        : "Connector";
    case "power":
      if (/\bcharger\b/i.test(text)) return "Charger";
      if (/\bregulator\b|\bldo\b|\bregulates?\b/i.test(text))
        return "Voltage regulator";
      if (/\bconverter\b|steps?[- ]down/i.test(text)) return "Power converter";
      return "Power supply";
    case "controller":
      // Explicitly provided capabilities belong to the controller; capabilities
      // after "for/to/from" may belong to a different component it serves.
      return /wi[- ]?fi|bluetooth|wireless/i.test(text) ||
        descriptions.some((description) =>
          /\b(?:with|providing)\s+(?:integrated\s+)?(?:wi[- ]?fi|bluetooth|wireless)\b/i.test(
            description.split(/\b(?:for|to|from)\b/i)[0],
          ),
        )
        ? "Wireless controller"
        : "Controller";
    case "sensor":
      if (/temperature/i.test(text) && /humidity/i.test(text))
        return "Temperature & humidity";
      if (/temperature|thermometer/i.test(text)) return "Temperature sensor";
      if (/humidity/i.test(text)) return "Humidity sensor";
      if (/ambient light|light sensor/i.test(text)) return "Light sensor";
      return "Sensor";
    default:
      if (/\bbattery (?:holder|retainer)\b/i.test(text))
        return "Battery holder";
      if (/\bbattery\b|\bcoin cell\b/i.test(text)) return "Battery";
      if (/\bdisplay\b|\boled\b/i.test(text)) return "Display";
      if (/\bbuzzer\b/i.test(text)) return "Buzzer";
      if (/\bsounds?\b.*\balarm\b/i.test(text)) return "Audible alarm";
      if (
        /\bmotor (?:driver|bridge)\b|\b(?:h|half)[- ]bridge\b|\bdriver\b.*\bmotors?\b/i.test(
          text,
        )
      )
        return "Motor driver";
      if (/\b(?:pushbutton|push button|switch)\b/i.test(text)) return "Switch";
      if (/\bresistor\b/i.test(text)) return "Resistor";
      if (/\bcapacitor\b/i.test(text)) return "Capacitor";
      // A sentence describing the whole device is useful in the inspector, not
      // as a map label. Keep unfamiliar parts honest without inventing a role.
      return part.name.trim() &&
        part.name !== part.product?.mpn &&
        part.name.length <= 36
        ? part.name
        : "Component";
  }
}
