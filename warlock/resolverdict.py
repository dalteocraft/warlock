

class ResolverDict(dict):

    def __init__(self, *args, **kwargs):
        super(ResolverDict, self).__init__(*args, **kwargs)
        self.resolver = None

    def __getitem__(self, key):
        internalKeys = super(ResolverDict, self).keys()
        if "$ref" in internalKeys:
            ref = super(ResolverDict, self).__getitem__("$ref")
            _, resolved = self.resolver.resolve(ref)
            if resolved is self:
                value = super(ResolverDict, self).__getitem__(key)
            else:
                value = resolved[key]
        else:
            value = super(ResolverDict, self).__getitem__(key)
        if isinstance(value, dict):
            value = ResolverDict(value)
            value.resolver = self.resolver
        return value
    
    def keys(self):
        if "$ref" in self:
            ref = super(ResolverDict, self).__getitem__("$ref")
            _, resolved = self.resolver.resolve(ref)
            if resolved is self:
                return super(ResolverDict, self).keys()
            return resolved.keys()
        else:
            return super(ResolverDict, self).keys()
    
    def __iter__(self):
        for key in self.keys():
            yield key
        
