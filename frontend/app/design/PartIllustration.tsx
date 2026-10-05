import type { ComponentRole } from "./componentPresentation";
import "./PartIllustration.css";

// One 30° projection keeps every symbolic component on the same drawing plane.
const projectPoint = (x: number, y: number, z: number) =>
  `${110 + (x - y) * 0.866},${29 + (x + y) * 0.5 - z}`;
const getPlaneTransform = (z: number) =>
  `matrix(.866 .5 -.866 .5 110 ${29 - z})`;

function Block({
  x,
  y,
  width,
  depth,
  z = 4,
  height,
  board = false,
}: {
  x: number;
  y: number;
  width: number;
  depth: number;
  z?: number;
  height: number;
  board?: boolean;
}) {
  const x2 = x + width;
  const y2 = y + depth;
  const top = z + height;
  return (
    <g className={board ? "technical-board" : "technical-package"}>
      <polygon
        className="technical-front"
        points={[
          projectPoint(x, y2, z),
          projectPoint(x2, y2, z),
          projectPoint(x2, y2, top),
          projectPoint(x, y2, top),
        ].join(" ")}
      />
      <polygon
        className="technical-side"
        points={[
          projectPoint(x2, y, z),
          projectPoint(x2, y2, z),
          projectPoint(x2, y2, top),
          projectPoint(x2, y, top),
        ].join(" ")}
      />
      <polygon
        className="technical-top"
        points={[
          projectPoint(x, y, top),
          projectPoint(x2, y, top),
          projectPoint(x2, y2, top),
          projectPoint(x, y2, top),
        ].join(" ")}
      />
    </g>
  );
}

/** Functional illustrations, not package drawings, pin assignments, or wiring diagrams. */
export default function PartIllustration({
  role,
  wireless = false,
  usb = false,
}: {
  role: ComponentRole;
  wireless?: boolean;
  usb?: boolean;
}) {
  return (
    <svg
      className={`part-illustration part-illustration-${role} technical-part`}
      viewBox="42 21 161 104"
      aria-hidden="true"
      focusable="false"
    >
      {role === "controller" ? (
        <>
          <Block x={7} y={4} width={95} depth={73} z={0} height={4} board />
          <g transform={getPlaneTransform(4)}>
            <path
              className="technical-trace"
              d="M91 14H96V31H87M88 43H96V60H83M68 65V70H43M34 45H24V67H15"
            />
            {wireless ? (
              <path
                className="technical-accent-line"
                d="M16 58V13H27V23H20V33H27V43H20V51H29"
              />
            ) : (
              <path className="technical-trace" d="M15 15H25V27H16V41H26V53" />
            )}
            <path className="technical-pad" d="M46 73H58M69 73H81" />
          </g>
          <Block x={35} y={18} width={51} depth={43} height={13} />
          <g transform={getPlaneTransform(17)}>
            <rect
              className="technical-seam"
              x="39"
              y="22"
              width="43"
              height="35"
            />
            <path className="technical-detail" d="M45 29H62M45 34H55" />
            <rect
              className="technical-accent-fill"
              x="71"
              y="48"
              width="5"
              height="3"
            />
          </g>
          <Block x={19} y={57} width={10} depth={7} height={3} />
          <Block x={31} y={66} width={8} depth={5} height={2} />
        </>
      ) : role === "sensor" ? (
        <>
          <Block x={12} y={7} width={82} depth={74} z={0} height={4} board />
          <g transform={getPlaneTransform(4)}>
            <path
              className="technical-trace"
              d="M24 18H43V26M77 19H85V45H76M28 48H20V69H43V61M67 61V73H82"
            />
            <path className="technical-accent-line" d="M77 52H85V63" />
            <path className="technical-pad" d="M45 77H55M62 77H72" />
          </g>
          <Block x={31} y={27} width={43} depth={34} height={11} />
          <g transform={getPlaneTransform(15)}>
            <rect
              className="technical-seam"
              x="35"
              y="31"
              width="35"
              height="26"
            />
            <path className="technical-vent" d="M45 39H58M45 43H58M45 47H58" />
            <rect
              className="technical-accent-fill"
              x="63"
              y="50"
              width="3"
              height="3"
            />
          </g>
          <Block x={24} y={65} width={10} depth={6} height={3} />
        </>
      ) : role === "power" ? (
        <>
          <Block x={12} y={7} width={82} depth={74} z={0} height={4} board />
          <g transform={getPlaneTransform(4)}>
            <path
              className="technical-trace"
              d="M24 18H50V27M78 19H85V48H77M29 45H21V69H45V66M62 66V74H82"
            />
            <path className="technical-accent-line" d="M68 24V17H59" />
            <path className="technical-pad" d="M28 75H39M69 77H79" />
            <path
              className="technical-terminal"
              d="M36 25V34M48 25V34M61 25V34M36 60V70M48 60V70M61 60V70"
            />
          </g>
          <Block x={31} y={31} width={42} depth={31} height={8} />
          <g transform={getPlaneTransform(12)}>
            <rect
              className="technical-seam"
              x="35"
              y="35"
              width="34"
              height="23"
            />
            <path className="technical-detail" d="M41 41H59M41 45H52" />
            <rect
              className="technical-accent-fill"
              x="61"
              y="51"
              width="4"
              height="3"
            />
          </g>
          <Block x={67} y={13} width={13} depth={8} height={3} />
        </>
      ) : role === "connector" ? (
        <>
          <Block x={10} y={7} width={89} depth={75} z={0} height={4} board />
          <g transform={getPlaneTransform(4)}>
            <path
              className="technical-trace"
              d="M30 27V15H64V25M73 26V17H87V54M17 50V70H21"
            />
            <path className="technical-pad" d="M31 78H41M72 78H82" />
          </g>
          <Block x={20} y={30} width={62} depth={43} height={22} />
          <g transform={getPlaneTransform(26)}>
            <path className="technical-seam" d="M24 36H78V66H24Z" />
            <path className="technical-detail" d="M31 41H44M58 41H71" />
          </g>
          <g
            transform={`matrix(.866 .5 0 -1 ${110 - 73 * 0.866} ${29 + 73 * 0.5})`}
          >
            <rect
              className="technical-socket"
              x="26"
              y="8"
              width="50"
              height="14"
              rx={usb ? 7 : 1}
            />
            <rect
              className="technical-tongue"
              x="34"
              y="13"
              width="34"
              height="3"
              rx={usb ? 1.5 : 0}
            />
          </g>
        </>
      ) : (
        <>
          <Block x={12} y={7} width={82} depth={74} z={0} height={4} board />
          <g transform={getPlaneTransform(4)}>
            <path
              className="technical-trace"
              d="M24 18H43V27M78 18H85V47H75M29 49H21V69H44V64M64 65V74H82"
            />
            <path
              className="technical-terminal"
              d="M26 36H37M26 47H37M26 57H37M69 36H81M69 47H81M69 57H81"
            />
          </g>
          <Block x={33} y={28} width={40} depth={36} height={9} />
          <g transform={getPlaneTransform(13)}>
            <rect
              className="technical-seam"
              x="37"
              y="32"
              width="32"
              height="28"
            />
            <path className="technical-detail" d="M43 39H60M43 44H53" />
            <rect
              className="technical-accent-fill"
              x="61"
              y="53"
              width="3"
              height="3"
            />
          </g>
        </>
      )}
    </svg>
  );
}
