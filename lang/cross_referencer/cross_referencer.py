from pathlib import Path
from typing import Dict, List

from lang.cross_referencer.models import Function, Struct, Unresolved
from lang.parser import models as parser


class CrossReferencer:
    def __init__(self, parser_output: parser.ParserOutput) -> None:
        self.parsed_files = parser_output.parsed
        self.builtins_path = parser_output.builtins_path

        self.structs: Dict[Path, Dict[str, Struct]] = {}
        self.functions: Dict[Path, Dict[str, Function]] = {}

    def run(self) -> None:
        for file, parsed in self.parsed_files.items():
            self.structs[file] = self._load_structs(parsed.structs)
            self.functions[file] = self._load_functions(parsed.functions)
            # TODO load imports

        # TODO find naming collisions between structs/functions/imports

        # TODO Resolve field types of structs

        # TODO argument/return types of functions

        # TODO resolve identifiers in functions

        # TODO handle exceptions
        ...

    def _load_structs(self, parsed_structs: List[parser.Struct]) -> Dict[str, Struct]:
        structs: Dict[str, Struct] = {}

        for parsed_struct in parsed_structs:
            struct = Struct(
                parsed=parsed_struct,
                fields={name: Unresolved() for (name, _) in parsed_struct.fields},
            )

            if parsed_struct.name in structs:
                # TODO naming conflict
                raise NotImplementedError

            structs[parsed_struct.name] = struct

        return structs

    def _load_functions(
        self, parsed_functions: List[parser.Function]
    ) -> Dict[str, Function]:
        functions: Dict[str, Function] = {}

        for parsed_function in parsed_functions:
            arguments: Dict[str, Unresolved] = {}

            for parsed_argument in parsed_function.arguments:

                if parsed_argument.name in arguments:
                    # TODO naming conflict
                    raise NotImplementedError

                arguments[parsed_argument.name] = Unresolved()

            function = Function(
                parsed=parsed_function,
                name=parsed_function.get_name(),
                type_name=parsed_function.get_type_name(),
                arguments=arguments,
                body=Unresolved(),
            )

            identifier = function.identify()

            if identifier in functions:
                # TODO naming conflict
                raise NotImplementedError

            functions[identifier] = function

        return functions
