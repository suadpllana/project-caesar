"""Which partitions exist.

A partition exists once it has ended by now and for `keep` hours after that - while
end <= now < end + keep. A published partition is never deleted, so it exists as soon as it has
ended, whatever its keep.
"""
from plan.span import ends


def there(pp, name, i):
    if i < 0:
        return False
    end = ends(pp, name, i)
    if end > pp.now:
        return False
    return (name, i) in pp.pins or pp.now < end + pp.keep[name]
