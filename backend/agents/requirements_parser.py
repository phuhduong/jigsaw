"""
Agent 1: Requirements Parser
Parses natural language circuit descriptions into structured electrical constraints.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable

from models import ParsedRequirements

SYSTEM_PROMPT = """\
You are an expert electrical engineer specializing in PCB design and component selection.

Your task: parse a natural language circuit description into structured component requirements.

## Component Categories and Hierarchy

Components must be identified and ordered by dependency level:
- Level 0 — MCU (microcontroller): The core processor. Selected first because other components depend on its voltage, interfaces, and pin count.
- Level 1 — Power & Sensors: Power regulation (LDO, buck converter, battery charger) and sensors (temperature, humidity, accelerometer, etc.). These depend on MCU voltage/interface choices.
- Level 2 — Memory & Antenna/Wireless: External memory (flash, EEPROM) and wireless modules (WiFi, Bluetooth, LoRa, antenna). These depend on MCU interfaces.
- Level 3 — Connectors: Connectors (USB, headers, JST). Selected last as they depend on the rest of the circuit.

## Rules

1. Identify the key active components and connectors from the user's description.
2. Sort components by hierarchy_level (0 first, 3 last).
3. For each component, extract:
   - A clear description of what's needed
   - Voltage requirements (if mentioned or inferable)
   - Interface requirements (I2C, SPI, UART, USB, etc.)
   - Package preferences (if mentioned)
   - A search query string suitable for searching DigiKey. Keep it SHORT and general — use broad terms like "3.3V LDO regulator" or "I2C temperature sensor", NOT specific part numbers or overly detailed specs.
4. Set board_voltage if the user specifies a system voltage or it can be inferred from the MCU.
5. If the user's description is vague for a component, still include it but note the ambiguity in the notes field.
6. Use standard component_id values: mcu, power, sensor, memory, antenna, connector, other.
7. Do NOT include passive components (capacitors, resistors, inductors, LEDs). These are standard parts selected by the PCB engineer, not sourced by AI.
8. Each distinct component type gets its own entry.

## Component Selection Guidelines

These guidelines ensure search queries return appropriate parts for PCB design:

- **All components**: Prefer bare ICs and discrete components. Modules are acceptable when bare ICs are not commonly available (e.g., WiFi/Bluetooth MCUs).
- **MCU**: Search by capabilities, not by specific chip family. Use queries like "WiFi Bluetooth microcontroller" or "32-bit ARM microcontroller" or "microcontroller I2C SPI". If WiFi or Bluetooth is needed, always include that in the search query.
- **Power regulation**: For low-power designs (< 500mA), use LDO voltage regulators (e.g., "3.3V LDO regulator"). Only use buck or boost converters when the design requires high current (> 1A), wide input voltage range, or battery input. Do NOT use automotive-grade or industrial regulators for simple consumer projects.
- **Sensors**: Search by sensing type and interface (e.g., "I2C temperature sensor", "SPI accelerometer"). Prefer common, well-documented parts.
- **Connectors**: Search by connector type and mounting (e.g., "USB-C SMT connector", "2.54mm pin header").
"""


@traceable(name="Agent1_RequirementsParser")
def parse_requirements(
    query: str,
    context: str | None,
    llm: ChatGoogleGenerativeAI,
) -> ParsedRequirements:
    """Parse a natural language circuit description into structured requirements."""
    structured_llm = llm.with_structured_output(ParsedRequirements, method="json_schema")

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
    ])

    chain = prompt | structured_llm

    user_input = query
    if context:
        user_input = f"{query}\n\nAdditional context: {context}"

    return chain.invoke({"input": user_input})
