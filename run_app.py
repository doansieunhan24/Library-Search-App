#!/usr/bin/env python3
"""
Library Search Application Launcher
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from main_app import LibrarySearchApp
from search_processor import SearchProcessor
from config import LOG_LEVEL, LOG_FORMAT, WINDOW_TITLE

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'PyQt6',
        'torch',
        'transformers',
        'openai',
        'sqlite3',
        'pyaudio',
        'speech_recognition'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        error_msg = f"Missing required modules: {', '.join(missing_modules)}\n"
        error_msg += "Please install them using: pip install -r requirements.txt"
        return False, error_msg
    
    return True, "All dependencies are available"

def test_connections():
    """Test all system connections"""
    try:
        processor = SearchProcessor()
        status = processor.test_connection()
        processor.close()
        
        failed_connections = [name for name, success in status.items() if not success]
        
        if failed_connections:
            warning_msg = f"Some connections failed: {', '.join(failed_connections)}\n"
            warning_msg += "The app may have limited functionality."
            return False, warning_msg
        
        return True, "All connections successful"
        
    except Exception as e:
        return False, f"Connection test failed: {str(e)}"

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Library Search Application...")
    
    # Check dependencies
    deps_ok, deps_msg = check_dependencies()
    if not deps_ok:
        print(f"Error: {deps_msg}")
        sys.exit(1)
    
    logger.info("All dependencies are available")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)
    
    # Test connections
    conn_ok, conn_msg = test_connections()
    if not conn_ok:
        reply = QMessageBox.warning(
            None,
            "Connection Warning",
            f"{conn_msg}\n\nDo you want to continue anyway?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.No:
            logger.info("User chose to exit due to connection issues")
            sys.exit(0)
        
        logger.warning(conn_msg)
    else:
        logger.info("All connections successful")
    
    # Create and show main window
    try:
        window = LibrarySearchApp()
        window.show()
        
        logger.info("Application window created and shown")
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        QMessageBox.critical(
            None,
            "Application Error",
            f"Failed to start application:\n{str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
