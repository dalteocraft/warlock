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

"""Self-validating model for arbitrary objects"""

import copy
import warnings

import jsonpatch
import jsonschema

from . import exceptions


class Model(dict):
    def __init__(self, *args, **kwargs):
        # we overload setattr so set this manually
        d = dict(*args, **kwargs)

        try:
            self.validate(d)
        except exceptions.ValidationError as exc:
            raise ValueError(str(exc))
        else:
            dict.__init__(self, d)

        self.__dict__["changes"] = {}
        self.__dict__["__original__"] = copy.deepcopy(d)
    
    def __getitem__(self, key):
        try:
            return super(Model, self).__getitem__(key)
        except KeyError:
            if key in self.schema["properties"] and "default" in self.schema["properties"][key]:
                return self.schema["properties"][key]["default"]
            raise

    def __setitem__(self, key, value):
        mutation = dict(self.items())
        mutation[key] = value
        try:
            self.validate(mutation)
        except exceptions.ValidationError as exc:
            msg = "Unable to set '%s' to %r. Reason: %s" % (key, value, str(exc))
            raise exceptions.InvalidOperation(msg)

        dict.__setitem__(self, key, value)

        self.__dict__["changes"][key] = value

    def __delitem__(self, key):
        mutation = dict(self.items())
        del mutation[key]
        try:
            self.validate(mutation)
        except exceptions.ValidationError as exc:
            msg = "Unable to delete attribute '%s'. Reason: %s" % (key, str(exc))
            raise exceptions.InvalidOperation(msg)

        dict.__delitem__(self, key)

    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __delattr__(self, key):
        self.__delitem__(key)

    # BEGIN dict compatibility methods

    def clear(self):
        raise exceptions.InvalidOperation()

    def pop(self, key, default=None):
        raise exceptions.InvalidOperation()

    def popitem(self):
        raise exceptions.InvalidOperation()

    def copy(self):
        return copy.deepcopy(dict(self))

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        return copy.deepcopy(dict(self), memo)

    def update(self, other):
        mutation = dict(self.items())
        mutation.update(other)
        try:
            self.validate(mutation)
        except exceptions.ValidationError as exc:
            raise exceptions.InvalidOperation(str(exc))
        _other = {}
        for key, v in other.items():
            v = self.map_to_model(key, v)
            _other[key] = v
        dict.update(self, _other)

    def items(self):
        return copy.deepcopy(dict(self)).items()

    def values(self):
        return copy.deepcopy(dict(self)).values()
    
    def keys(self):
        tmpdict = {}
        for key in super(Model, self).keys():
            tmpdict[key] = None
        # Add all properties with default
        if "properties" in self.schema:
            for key, property_schema in self.schema["properties"].items():
                if key not in tmpdict and "default" in property_schema:
                    tmpdict[key] = None
        return tmpdict.keys()
    
    def __iter__(self):
        for key in self.keys():
            yield key





    # END dict compatibility methods

    @property
    def patch(self):
        """Return a jsonpatch object representing the delta"""
        original = self.__dict__["__original__"]
        return jsonpatch.make_patch(original, dict(self)).to_string()

    @property
    def changes(self):
        """Dumber version of 'patch' method"""
        deprecation_msg = "Model.changes will be removed in warlock v2"
        warnings.warn(deprecation_msg, DeprecationWarning, stacklevel=2)
        return copy.deepcopy(self.__dict__["changes"])

    def validate(self, obj):
        """Apply a JSON schema to an object"""
        try:
            self.validator_instance.validate(obj)

        except jsonschema.ValidationError as exc:
            raise exceptions.ValidationError(str(exc))
