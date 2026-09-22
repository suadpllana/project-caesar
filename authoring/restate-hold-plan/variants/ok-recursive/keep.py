from plan.span import ends


def there(pp, name, i):
    if i < 0:
        return False
    e = ends(pp, name, i)
    return e <= pp.now and ((name, i) in pp.pins or pp.now - e < pp.keep[name])
