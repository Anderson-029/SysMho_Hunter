"""
ToolRegistry — registro dinámico de herramientas.
Las tools se registran con el decorador @ToolRegistry.register
y se auto-descubren al importar el módulo tools/.
"""

from app.recon.base_tool import BaseTool


class ToolRegistry:
    _registry: dict[str, type[BaseTool]] = {}

    @classmethod
    def register(cls, tool_class: type[BaseTool]) -> type[BaseTool]:
        """Decorador para registrar una tool en el registro."""
        cls._registry[tool_class.name] = tool_class
        return tool_class

    @classmethod
    def get(cls, name: str) -> type[BaseTool] | None:
        return cls._registry.get(name)

    @classmethod
    def get_tools_for_phase(cls, phase: str) -> list[BaseTool]:
        """Retorna instancias de tools disponibles para una fase."""
        tools = []
        for tool_cls in cls._registry.values():
            if tool_cls.phase == phase:
                instance = tool_cls()
                if instance.is_installed():
                    tools.append(instance)
        return tools

    @classmethod
    def all_tools_status(cls) -> dict[str, dict]:
        """Retorna estado de todas las tools registradas."""
        status = {}
        for name, tool_cls in cls._registry.items():
            instance = tool_cls()
            status[name] = {
                "phase": tool_cls.phase,
                "risk_level": tool_cls.risk_level,
                "installed": instance.is_installed(),
            }
        return status

    @classmethod
    def _import_all_tools(cls) -> None:
        """Importa todos los módulos de tools/ para registrarlos."""
        import importlib
        import pkgutil

        import app.recon.tools as tools_pkg

        for _, module_name, _ in pkgutil.iter_modules(tools_pkg.__path__):
            importlib.import_module(f"app.recon.tools.{module_name}")


# Importar todas las tools al cargar el módulo
ToolRegistry._import_all_tools()
