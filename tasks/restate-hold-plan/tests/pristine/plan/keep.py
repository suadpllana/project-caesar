from plan.span import ends


def there(pp, name, i):
    if i < 0:
        return False
    end = ends(pp, name, i)
    return end <= pp.now and pp.now - end < pp.keep[name]
