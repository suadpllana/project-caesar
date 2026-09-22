def fire(book, bar, delta):
    lost = [bar.goal] if book.held(bar.goal) else []
    book.shut(bar.goal)
    return lost
