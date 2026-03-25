# Product Roadmap

This document outlines the development trajectory for the AeroSense project. Tasks are prioritized by execution window: **Immediate**, **Upcoming**, and **Long Term**.

## Immediate Tasks
- Add UA Fight Song
- Add UA Alma Mater.

---

## Upcoming Tasks

- Implement MOSS.
    - Framework: Implement an AI Agent (named MOSS) that you can chat with regarding the system. Have it frameworked by Ollama and choose a prebuilt model that will allow for fine tuning if needed (Maybe Gemma).
    - Purpose: This agent will have several prebuilt tools coded in Python that allow it to control the system, or inform the user of things going on within the system.
    - Interface: In the CLI, the user can type MOSS (Message). Any message begining with a Moss will be sent to the AI Agent, and an appropriate response will be sent back. Additionally, there will be a new chat box on the GUI, any message in here is automatically sent to the AI agent. Allow for a Agent Reset command that will kill the current conversation and start a new one.
    - Model: The model will have a based personality file. It will be informed of some of the general system capabilities, parameters, etc. However, we will also make some additional files to give it more knowledge on what is good and bad. Give it the ability to feel happy or sad and play music based on that and how plants are doing. It will also have some files regarding the users so it knows who we are.
    - Tools: Read any of the .md files to learn more about the system (Ex user asking about hardware, open hardware.md and read it). Read any of the model files (Ex user is asking about a user, read the file regarding the users.). Run the temp sensor. Run the distance sensor. Play any category of song (Ex when the model is happy play a random happy song). Run the vision command. Run the plant health command. Read the output of the vision command (maybe give it the ability to just read the relevant/most recent info from the .csv). Read the output of the plant health command (same as previous). Read the output of temp/dist (same as previous).
    - Outputs: It's purpose is to serve the user. It can offer suggestions based on what the output of the tools it has (Ex, plants need water, it reccomends increasing the water usage). It can also just provide information based on any of the model files or the .md files. It should be a fun companion that has its own distinct personality and is very helpful.
    - Need to be implemented as industry standard as possible. Think of all possible errors and edge cases. I am not set on this, willing to consider something else if a good argument is made. Must be coded simplely to allow for easy fine tuning, additional tools, and additional parameters. Should be stored in the ml folder with a new agent.py for the python, and have the model files stored in models folder.

- GUI full revamp.
    - Have each box able to be dropped down or not.
    - Have new sliders and graphs and just better information and whatnot.
    - Have it more consistent.
    - Maybe make it like a situation monitoring webpage.

- README.md full revamp.

---

## Long Term Tasks

---