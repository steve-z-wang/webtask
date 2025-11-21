"""Utilities for working with JSON schemas."""

from typing import Any, Dict


def resolve_json_schema_refs(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve $ref references in JSON schema by inlining definitions.

    Many LLM APIs (Gemini, Bedrock) don't support $ref references in tool schemas.
    This function resolves all $ref references by replacing them with their actual
    definitions from $defs.

    Args:
        schema: The JSON schema to resolve (typically from model_json_schema())

    Returns:
        Schema with all $ref references resolved inline

    Example:
        >>> from pydantic import BaseModel
        >>> class Item(BaseModel):
        ...     name: str
        >>> class Cart(BaseModel):
        ...     items: List[Item]
        >>>
        >>> schema = Cart.model_json_schema()
        >>> # schema has: {"properties": {"items": {"items": {"$ref": "#/$defs/Item"}}}, "$defs": {...}}
        >>>
        >>> resolved = resolve_json_schema_refs(schema)
        >>> # resolved has: {"properties": {"items": {"items": {"type": "object", "properties": {...}}}}}
    """
    if not isinstance(schema, dict):
        return schema

    # Extract $defs for reference resolution
    defs = schema.get("$defs", {})

    def resolve_refs_recursive(obj: Any) -> Any:
        """Recursively resolve $ref references."""
        if isinstance(obj, dict):
            # If this is a $ref, resolve it
            if "$ref" in obj:
                ref_path = obj["$ref"]
                # Handle #/$defs/ModelName format
                if ref_path.startswith("#/$defs/"):
                    def_name = ref_path.split("/")[-1]
                    if def_name in defs:
                        # Return the resolved definition (recursively)
                        return resolve_refs_recursive(defs[def_name])
                return obj  # Can't resolve, return as-is

            # Recursively resolve in all values
            return {k: resolve_refs_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve_refs_recursive(item) for item in obj]
        else:
            return obj

    # Resolve refs in the main schema
    resolved = resolve_refs_recursive(schema)

    # Remove $defs from the result (no longer needed)
    if isinstance(resolved, dict) and "$defs" in resolved:
        resolved = {k: v for k, v in resolved.items() if k != "$defs"}

    return resolved
