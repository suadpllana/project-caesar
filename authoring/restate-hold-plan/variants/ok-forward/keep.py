from plan.span import ends


def there(pp, name, i):
    if i < 0:
        return False
    end = ends(pp, name, i)
    if end > pp.now:
        return False
    if (name, i) in pp.pins:
        return True
    return end + pp.keep[name] > pp.now
