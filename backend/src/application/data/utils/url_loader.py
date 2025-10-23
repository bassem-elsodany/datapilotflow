"""
URL loader utility for single_page scraping mode.

This module provides functionality to load URLs from different sources
(file, inline) for single_page scraping mode.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger


class URLLoader:
    """Utility class for loading URLs from different sources."""
    
    @staticmethod
    def load_urls(url_source_config) -> List[str]:
        """Load URLs based on the URL source configuration.
        
        Args:
            url_source_config: Configuration dict or Pydantic object with type, path, format, etc.
            
        Returns:
            List[str]: List of URLs to process
            
        Raises:
            ValueError: If configuration is invalid or file not found
        """
        # Handle both dict and Pydantic objects
        
        if hasattr(url_source_config, 'dict'):
            # Pydantic object - convert to dict
            config_dict = url_source_config.dict()
        elif hasattr(url_source_config, 'model_dump'):
            # Pydantic v2 object - convert to dict
            config_dict = url_source_config.model_dump()
        else:
            # Already a dict
            config_dict = url_source_config
            
        source_type = config_dict.get('type')
        
        # Handle UrlSourceConfig objects that don't have a type field
        if source_type is None and 'urls' in config_dict:
            logger.debug("Detected UrlSourceConfig object with inline URLs")
            return URLLoader._load_inline(config_dict)
        elif source_type == 'file':
            return URLLoader._load_from_file(config_dict)
        elif source_type == 'inline':
            return URLLoader._load_inline(config_dict)
        else:
            raise ValueError(f"Unsupported URL source type: {source_type}")
    
    @staticmethod
    def _load_from_file(config: Dict[str, Any]) -> List[str]:
        """Load URLs from a file.
        
        Args:
            config: Configuration with 'path' and 'format' keys
            
        Returns:
            List[str]: List of URLs from the file
        """
        file_path = config.get('path')
        file_format = config.get('format')
        
        if not file_path:
            raise ValueError("File path is required for file URL source")
        if not file_format:
            raise ValueError("File format is required for file URL source")
        
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"URL file not found: {file_path}")
        
        logger.info(f"Loading URLs from file: {file_path} (format: {file_format})")
        
        if file_format == 'line_by_line':
            return URLLoader._load_line_by_line(path)
        elif file_format == 'json':
            return URLLoader._load_json(path)
        elif file_format == 'csv':
            return URLLoader._load_csv(path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
    
    @staticmethod
    def _load_line_by_line(path: Path) -> List[str]:
        """Load URLs from a file with one URL per line."""
        urls = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    urls.append(line)
        
        logger.info(f"Loaded {len(urls)} URLs from line-by-line file")
        return urls
    
    @staticmethod
    def _load_json(path: Path) -> List[str]:
        """Load URLs from a JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            urls = data
        elif isinstance(data, dict) and 'urls' in data:
            urls = data['urls']
        else:
            raise ValueError("JSON file must contain a list of URLs or a dict with 'urls' key")
        
        logger.info(f"Loaded {len(urls)} URLs from JSON file")
        return urls
    
    @staticmethod
    def _load_csv(path: Path) -> List[str]:
        """Load URLs from a CSV file."""
        urls = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():  # Skip empty rows
                    urls.append(row[0].strip())
        
        logger.info(f"Loaded {len(urls)} URLs from CSV file")
        return urls
    
    @staticmethod
    def _load_inline(config: Dict[str, Any]) -> List[str]:
        """Load URLs from inline configuration.
        
        Args:
            config: Configuration with 'urls' key containing list of URLs
            
        Returns:
            List[str]: List of URLs from the configuration
        """
        urls = config.get('urls', [])
        
        if not isinstance(urls, list):
            raise ValueError("Inline URLs must be a list")
        
        logger.info(f"Loaded {len(urls)} URLs from inline configuration")
        return urls 