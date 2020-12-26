# Copyright 2012 Brian Waldon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Core Warlock functionality"""

import copy

from . import model
from .resolverdict import ResolverDict
from jsonschema.validators import validator_for


def model_factory(schema, base_class=model.Model, name=None, resolver=None):
    """Generate a model class based on the provided JSON Schema

    :param schema: dict representing valid JSON schema
    :param name: A name to give the class, if `name` is not in `schema`
    """
    schema = copy.deepcopy(schema)
    resolver = resolver

    class Model(base_class):
        properties_classes = {}

        def __init__(self, *args, **kwargs):
            self.__dict__["schema"] = schema
            self.__dict__["resolver"] = resolver

            cls = validator_for(self.schema)
            if resolver is not None:
                self.__dict__["validator_instance"] = cls(schema, resolver=resolver)
            else:
                self.__dict__["validator_instance"] = cls(schema)
            args_dict = dict(*args)
            _kwargs = {}
            for key, v in args_dict.items():
                v = self.map_to_model(key, v)
                _kwargs[key] = v
            for key, v in kwargs.items():
                v = self.map_to_model(key, v)
                _kwargs[key] = v

            base_class.__init__(self, _kwargs)

        def map_to_model(self, key, value):
            # TODO find a way to implement map_to_model on the base class. But map_to_model needs access model_factory function.
            schema = ResolverDict(self.schema)
            schema.resolver = self.resolver
            if "properties" in schema and key in schema["properties"] and schema["properties"][key]["type"] == "object":
                if key not in Model.properties_classes:
                    Model.properties_classes[key] = model_factory(schema["properties"][key], base_class=base_class, resolver=resolver)
                value = Model.properties_classes[key](**value)
            return value
        
        def __setitem__(self, key, value):
            value = self.map_to_model(key, value)
            super(Model, self).__setitem__(key, value)

    if resolver is not None:
        Model.resolver = resolver

    if name is not None:
        Model.__name__ = name
    elif "name" in schema:
        Model.__name__ = str(schema["name"])
    return Model
