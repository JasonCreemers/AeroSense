"""
AeroSense Main Entry Point.

This module serves as the application bootstrapper. 
It initializes the logging system, instantiates core subsystems, and launches the Command Line Interface (CLI) in the main thread.
"""

import logging
import sys
import time

import aerosense
from aerosense import Controller, Scheduler, CLI


def main():
    """
    Main application execution entry point.
    """
    # --- Setup Logging ---
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(name)s - %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    log = logging.getLogger("AeroSense.Main")
    
    print(f"\n=== AEROSENSE GARDEN CONTROLLER V{aerosense.__version__} | ({aerosense.__release__}) ===")
    log.info("System initializing...")

    # --- Start and Run Application ---
    try:
        # Initialize core systems
        # The Controller manages hardware state
        controller = Controller()
        
        # The Scheduler manages automation logic
        scheduler = Scheduler(controller)
        
        # The CLI manages user input
        cli = CLI(controller, scheduler)

        # --- Start Interface ---
        cli.start()
        
        log.info("System Active.")

        # --- Main Automation Loop ---
        while cli.running:
            # Check schedule for automated tasks
            scheduler.update()
            
            # Monitor hardware safety
            controller.update()
            
            time.sleep(0.1)

    except KeyboardInterrupt:
        # Handle user-initiated shutdown via Ctrl+C
        print("\n")
        log.info("Shutdown signal received (Ctrl+C).")
        
    except Exception as e:
        # Catch unexpected runtime errors
        log.critical(f"Fatal Error: {e}", exc_info=True)
        
    finally:
        # Ensure hardware is turned off safely before process exit
        if 'controller' in locals():
            controller.stop_all()
            
        print(">> System Shutdown Complete.")
        sys.exit(0)


if __name__ == "__main__":
    main()