import re
import keyword
from enum import Enum
from typing import List, Optional


class Identifier:
    counter = {}

    @staticmethod
    def make_identifier(name: str) -> str:
        # Replace invalid characters
        identifier = re.sub('[^0-9a-zA-Z_]', '_', name.lower())

        # Remove leading underscores
        identifier = identifier.lstrip('_')

        # If the identifier starts with a digit, prefix with an underscore
        if identifier[0].isdigit():
            identifier = '_' + identifier

        # If the identifier is a Python keyword, prefix with an underscore
        if keyword.iskeyword(identifier):
            identifier = '_' + identifier

        # Append counter if identifier already exists
        if identifier in Identifier.counter:
            Identifier.counter[identifier] += 1
            identifier = f"{identifier}_{Identifier.counter[identifier]}"
        else:
            Identifier.counter[identifier] = 1
        
        return identifier
    

class Dumper:
    def __init__(self):
        self.level = 0
        self.lines = []

    def add(self, s: str) -> None:
        self.lines.append(f'{"  " * self.level}{s}')

    def indent(self) -> None:
        self.level += 1

    def outdent(self):
        self.level -= 1
        if self.level < 0:
            self.level = 0

    def result(self) -> str:
        return "\n".join(self.lines)


class Element:
    def __init__(self, name: str, description: Optional[str]=None, technology: Optional[str]=None, tags: Optional[List[str]]=None):
        self.name = name
        self.description = description if description else ""
        self.technology = technology if technology else ""
        self.tags = tags if tags else []
        self.relationships = []
        self.instname = Identifier.make_identifier(name)

    def uses(self, destination: str, description: Optional[str]=None, technology: Optional[str]=None) -> 'Relationship':
        relationship = Relationship(self, destination, description, technology)
        self.relationships.append(relationship)
        return relationship
    
    def dump(self, dumper: Dumper) -> None:
        raise NotImplementedError("This method must be implemented in a subclass.")

    def dump_relationships(self, dumper: Dumper) -> None:
        raise NotImplementedError("This method must be implemented in a subclass.")


class Person(Element):
    def __init__(self, name: str, description: Optional[str]=None, technology: Optional[str]=None, tags: Optional[List[str]]=None):
        super().__init__(name, description, technology, tags)

    def dump(self, dumper: Dumper) -> None:
        dumper.add(f'{self.instname} = Person "{self.name}" "{self.description}" {{')
        dumper.indent()
        if self.technology:
            dumper.add(f'technology "{self.technology}"')
        if self.tags:
            dumper.add(f'tags "{", ".join(self.tags)}"')
        dumper.outdent()
        dumper.add(f'}}')

    def dump_relationships(self, dumper: Dumper) -> None:
        for rel in self.relationships:
            rel.dump(dumper)


class Component(Element):
    def __init__(self, name: str, description: Optional[str]=None, technology: Optional[str]=None, tags: Optional[List[str]]=None):
        super().__init__(name, description, technology, tags)

    def dump(self, dumper: Dumper) -> None:
        dumper.add(f'{self.instname} = Component "{self.name}" "{self.description}" {{')
        dumper.indent()
        if self.technology:
            dumper.add(f'technology "{self.technology}"')
        if self.tags:
            dumper.add(f'tags "{", ".join(self.tags)}"')
        dumper.outdent()
        dumper.add(f'}}')

    def dump_relationships(self, dumper: Dumper) -> None:
        for rel in self.relationships:
            rel.dump(dumper)


class Container(Element):
    def __init__(self, name: str, description: Optional[str]=None, technology: Optional[str]=None, tags: Optional[List[str]]=None):
        super().__init__(name, description, technology, tags)
        self.components = []

    def Component(self, *args, **kwargs) -> Component:
        if args and isinstance(args[0], Component):
            component = args[0]
        else:
            component = Component(*args, **kwargs)
        self.components.append(component)
        return component

    def dump(self, dumper: Dumper) -> None:
        dumper.add(f'{self.instname} = Container "{self.name}" "{self.description}" {{')
        dumper.indent()
        if self.technology:
            dumper.add(f'technology "{self.technology}"')
        if self.tags:
            dumper.add(f'tags "{", ".join(self.tags)}"')
        for component in self.components:
            component.dump(dumper)
        dumper.outdent()
        dumper.add(f'}}')

    def dump_relationships(self, dumper: Dumper) -> None:
        for rel in self.relationships:
            rel.dump(dumper)
        for component in self.components:
            component.dump_relationships(dumper)


class SoftwareSystem(Element):
    def __init__(self, name: str, description: Optional[str]=None, technology: Optional[str]=None, tags: Optional[List[str]]=None):
        super().__init__(name, description, technology, tags)
        self.containers = []

    def Container(self, *args, **kwargs) -> Container:
        if args and isinstance(args[0], Container):
            container = args[0]
        else:
            container = Container(*args, **kwargs)
        self.containers.append(container)
        return container

    def dump(self, dumper: Dumper) -> None:
        dumper.add(f'{self.instname} = SoftwareSystem "{self.name}" "{self.description}" {{')
        dumper.indent()
        if self.technology:
            dumper.add(f'technology "{self.technology}"')
        if self.tags:
            dumper.add(f'tags "{", ".join(self.tags)}"')
        for container in self.containers:
            container.dump(dumper)
        dumper.outdent()
        dumper.add(f'}}')

    def dump_relationships(self, dumper: Dumper) -> None:
        for rel in self.relationships:
            rel.dump(dumper)
        for container in self.containers:
            container.dump_relationships(dumper)


class Model(Element):
    def __init__(self, name: str):
        super().__init__(name)
        self.elements = []

    def Person(self, *args, **kwargs) -> Person:
        if args and isinstance(args[0], Person):
            person = args[0]
        else:
            person = Person(*args, **kwargs)
        self.elements.append(person)
        return person

    def SoftwareSystem(self, *args, **kwargs) -> SoftwareSystem:
        if args and isinstance(args[0], SoftwareSystem):
            system = args[0]
        else:
            system = SoftwareSystem(*args, **kwargs)
        self.elements.append(system)
        return system

    def dump(self, dumper: Dumper) -> None:
        for element in self.elements:
            element.dump(dumper)

    def dump_relationships(self, dumper: Dumper) -> None:
        for element in self.elements:
            element.dump_relationships(dumper)


class Relationship:
    def __init__(self, source: Element, destination: Element, description: Optional[str]=None, technology: Optional[str]=None):
        self.source = source
        self.destination = destination
        self.description = description if description else "" 
        self.technology = technology if technology else ""

    def dump(self, dumper: Dumper) -> None:
        dumper.add(f'{self.source.instname} -> {self.destination.instname} "{self.description}" "{self.technology}"')


class View:
    class Kind(Enum):
        SYSTEM_LANDSCAPE = "systemLandscape"
        SYSTEM_CONTEXT = "systemContext"
        CONTAINER = "container"
        COMPONENT = "component"

    def __init__(self, viewkind: Kind, element: Element, name: str, description: Optional[str]=None):
        self.viewkind = viewkind
        self.element = element
        self.name = name
        self.description = description
        self.includes = []
        self.excludes = []

    def include(self, element: Element) -> 'View':
        self.includes.append(element)
        return self
        
    def exclude(self, element: Element) -> 'View':
        self.excludes.append(element)
        return self

    def dump(self, dumper: Dumper) -> None:
        dumper.add(f'{self.viewkind.value} {self.element.instname if self.element else ""} {{')
        dumper.indent()
        if self.description:
            dumper.add(f'description "{self.description}"')
        dumper.add('include *')
        for include in self.includes:
            dumper.add(f'include {include.instname}')
        for exclude in self.excludes:
            dumper.add(f'exclude {exclude.instname}')
        dumper.add('autoLayout')
        dumper.outdent()
        dumper.add(f'}}')


class Style:
    def __init__(self, map: dict[str, str]):
        self.map = map

    def dump(self, dumper: Dumper) -> None:
        dumper.add(f'element "{self.map["tag"]}" {{')
        dumper.indent()
        for k, v in self.map.items():
            if k == "tag":
                continue
            dumper.add(f'{k} "{v}"')
        dumper.outdent()
        dumper.add(f'}}')


class Workspace:
    def __init__(self):
        self.models = []
        self.views = []
        self.styles = []
        # Default styling
        self.Styles(
            {
                "tag": "Element",
                "shape": "RoundedBox"
            }, {
                "tag": "Software System",
                "background": "#1168bd",
                "color": "#ffffff"
            }, {
                "tag": "Container",
                "background": "#438dd5",
                "color": "#ffffff"
            }, {
                "tag": "Component",
                "background": "#85bbf0",
                "color": "#000000"
            }, {
                "tag": "Person",
                "background": "#08427b",
                "color": "#ffffff",
                "shape": "Person"
            }, {
                "tag": "Infrastructure Node",
                "background": "#ffffff"
            }, {
                "tag": "database",
                "shape": "Cylinder"
            }
        )

    def dump(self, dumper: Dumper = Dumper()) -> None:
        dumper.add(f'workspace {{')
        dumper.indent()

        dumper.add(f'model {{')
        dumper.indent()
        for model in self.models:
            model.dump(dumper)
        for model in self.models:
            model.dump_relationships(dumper)
        dumper.outdent()
        dumper.add(f'}}')

        dumper.add(f'views {{')
        dumper.indent()
        for view in self.views:
            view.dump(dumper)
        dumper.add(f'styles {{')
        dumper.indent()
        for style in self.styles:
            style.dump(dumper)
        dumper.outdent()
        dumper.add(f'}}')
        dumper.outdent()
        dumper.add(f'}}')

        dumper.outdent()
        dumper.add(f'}}')
        return dumper.result()

    def Model(self, model: Optional[Model]=None, name: Optional[str]=None):
        if model is None:
            model = Model(name)
        self.models.append(model)
        return model

    def SystemLandscapeView(self, name: str, description: str):
        view = View(View.Kind.SYSTEM_LANDSCAPE, None, name, description)
        self.views.append(view)
        return view
    
    def SystemContextView(self, element: Element, name: str, description: str):
        view = View(View.Kind.SYSTEM_CONTEXT, element, name, description)
        self.views.append(view)
        return view
    
    def ContainerView(self, element: Element, name: str, description: str):
        view = View(View.Kind.CONTAINER, element, name, description)
        self.views.append(view)
        return view
    
    def ComponentView(self, element: Element, name: str, description: str):
        view = View(View.Kind.COMPONENT, element, name, description)
        self.views.append(view)
        return view

    def Styles(self, *styles: dict[str, str]) -> None:
        for style in styles:
            self.styles.append(Style(style))
    