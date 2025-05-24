from jinja2 import Template as Jinja2Template
from pydantic import BaseModel


class Template(BaseModel):
    template: str

    def render(self):
        kwargs = self.__dict__
        template = kwargs.pop("template")
        return Jinja2Template(template).render(**kwargs)


class FieldTemplate(Template):
    template: str = """{{type}} {{name}} = {{index}};
"""

    type: str
    name: str
    index: int


class LabelFieldTemplate(FieldTemplate):
    template: str = """{{label}} {{type}} {{name}} = {{index}};
"""

    label: str


class DefaultFieldTemplate(FieldTemplate):
    template: str = """{{type}} {{name}} = {{index}} [default = {{default}}];
"""

    default: str


class LabelDefaultFieldTemplate(FieldTemplate):
    template: str = """{{label}} {{type}} {{name}} = {{index}} [default = {{default}}];
"""

    label: str
    default: str


class MessageTemplate(Template):
    template: str = """message {{name}} {
{%- for field in fields %}
    {{field-}}
{% endfor %}
}"""

    name: str
    fields: list[str]


class MethodTemplate(Template):
    template: str = """rpc {{name}} ({{request}}) returns ({{response}});
"""

    name: str
    request: str
    response: str


class ServiceTemplate(Template):
    template: str = """service {{name}} {
{%- for method in methods %}
    {{method-}}
{% endfor %}
}"""

    name: str
    methods: list[str]


class PackageTemplate(Template):
    template: str = """syntax = "proto3";

package {{name}};

{%- for import in imports %}
import "{{import}}";
{%- endfor %}

{%- for element in elements %}
{{element}}
{% endfor %}"""

    name: str
    imports: list[str]
    elements: list[str]


class EnumItemTemplate(Template):
    template: str = """{{name}} = {{index}};
"""

    name: str
    index: int


class EnumTemplate(Template):
    template: str = """enum {{name}} {
    // option allow_alias = true;
    ENUM_UNSPECIFIED = 0; // default value
{%- for item in items %}
    {{item-}}
{% endfor %}
}"""

    name: str
    items: list[str]


class OneOfTemplate(Template):
    template: str = """oneof {{name}} {
    {%- for field in fields %}
        {{field-}}
    {% endfor %}
    }"""

    name: str
    fields: list[str]


if __name__ == "__main__":
    print(
        FieldTemplate(
            type="int32",
            name="a",
            index=1,
        ).render()
    )
