# Fun Facts

Share these when the mood is right or when the user asks for something fun.

## Plant Facts
- Plants can "hear" — studies show they grow faster with music or gentle vibrations.
- The average houseplant can remove up to 87% of air toxins in 24 hours.
- Talking to plants may actually help them grow — the CO2 from your breath helps.
- Sunflowers track the sun across the sky (heliotropism) when they are young.
- The world's oldest known potted plant is over 240 years old.
- Plants can communicate with each other through underground fungal networks called the "Wood Wide Web."
- Bamboo can grow up to 35 inches in a single day — the fastest growing plant on Earth.
- Mint is so aggressive it can take over an entire garden if not contained.
- A single oak tree can produce around 70,000 acorns in a year.
- Venus flytraps can count — they only snap shut after two touches within 20 seconds.
- Grass releases a chemical distress signal when cut. That fresh-cut lawn smell is actually a cry for help.
- Some plants, like the sensitive plant (Mimosa pudica), can move their leaves when touched.

## Aeroponic Facts
- Aeroponics uses up to 95% less water than traditional soil gardening.
- Plant roots in aeroponic systems are suspended in air and misted with nutrient solution — no soil needed.
- NASA researched aeroponics in the 1990s as a way to grow food in space with minimal water and weight.
- Aeroponic plants can grow up to 3x faster than soil-grown plants due to increased oxygen exposure at the roots.
- The word "aeroponics" comes from the Greek words "aero" (air) and "ponos" (labor).
- Aeroponic systems virtually eliminate soil-borne diseases and pests since there is no soil.
- The first aeroponic patent was filed in 1983, but the concept was studied as early as the 1940s.
- Vertical aeroponic farms can produce more food per square foot than any other farming method.
- Because roots hang in open air, aeroponic plants absorb nutrients more efficiently than hydroponic or soil systems.
- Aeroponic misting intervals are typically only a few seconds long — just enough to keep roots damp without drowning them.

## AeroSense Facts
- AeroSense was built as a Senior Design project at the University of Akron, Mechanical Engineering Department Class of 2026.
- Senior Design Day is April 16, 2026.
- The system uses a dual-controller architecture: a Raspberry Pi 5 (16GB) for brains and an Arduino Mega 2560 for muscle.
- The Pi and Arduino communicate over serial UART at 115200 baud — about 14,400 characters per second.
- The vision system uses a 12MP IMX708 camera and can detect 5 plant diseases: chlorosis, necrosis, pest damage, tip burn, and wilting.
- AeroSense has a passive piezo buzzer that can play songs sorted by category — happy, sad, angry, and serious.
- The water level sensor is contactless — it uses ultrasonic sound waves to measure the reservoir without ever touching the water.
- The system enforces safety interlocks: the pump won't run if the water level is critically low, and max pump runtime is capped at 30 seconds.
- AeroSense logs everything — temperature, humidity, water level, pump activity, light cycles, vision results, and even what songs it plays.
- The XGBoost health classifier can diagnose 7 plant conditions: Healthy, Underwatered, Overwatered, More Light, Less Light, Nutrient Burn, and Pathogen.
- The system was on version 4.4.2 before MOSS was even born — it had a whole life before gaining the ability to talk.
- The environment sensor communicates over I2C at address 0x44 — it has its own little mailing address on the data bus.

## MOSS Facts
- MOSS is named after the AI from the movie Interstellar.
- MOSS runs entirely locally on the Pi using Ollama — no cloud, no internet required, full privacy.
- MOSS's birthday is March 25th, 2026.
- MOSS is powered by Gemma 3 4B, a model small enough to run on a Raspberry Pi but smart enough to diagnose plant problems.
- MOSS has moods — happy, concerned, thoughtful, worried, and alarmed — all driven by how the plants are doing.
- When MOSS's mood changes, it picks music to match. Happy plants get upbeat songs. Struggling plants get something more somber.
- MOSS can call up to 5 tools in a single response, but it has a safety cap to prevent infinite tool call loops.
- MOSS's brain takes up about 3GB of RAM. On a 16GB Pi 5, that leaves plenty of room for everything else.
- MOSS streams its responses token by token — you see it "thinking" in real time, just like a person typing.
- If nobody talks to MOSS for 30 minutes, it unloads from memory to save resources. It wakes back up on the next message.
- MOSS keeps a rolling conversation of 40 messages. Old messages quietly fall off the back — it never loses recent context.
- MOSS can read its own documentation files to answer questions about the system, the hardware, or even itself.
- MOSS was the last major feature added to AeroSense — the final piece that gave the garden a voice.
