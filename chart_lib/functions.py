
def p_obj(obj):
    print(f'{obj=}')

def generate_grid_specs(grid: tuple) -> list[list[None]]:
    """
    Creates a grid of Nones. e.g:
    2x3:
    [
    [None,None,None],
    [None,None,None]
    ]

    Args:
        grid (tuple): grid of two integer values,
        first to row, second to column.

    Returns:
        list[list[None]]: Grid of Nones
    """
    return [[None for _ in range(grid[1])] for _ in range(grid[0])]


def populate_grid_specs(grid_specs: list[list[dict]], list_objs: list[dict]) -> dict:
    obj_grid = {}
    for obj in list_objs:
        type_chart = obj['type']
        title = obj['title']
        x1, y1, x2, y2 = obj['coord']
        if x2 > x1:
            if y2 > y1:
                grid_specs[x1][y1] = {'rowspan': x2-x1+1, 'colspan': y2-y1+1, 'title': title}
            else: #means only equal (y2 = y1), never less
                grid_specs[x1][y1] = {'rowspan': x2-x1+1, 'title': title}
        else: #means only equal (x2 = x1), never less
            if y2 > y1:
                grid_specs[x1][y1] = {'colspan': y2-y1+1, 'title': title}
            else: #means only equal (y2 = y1), never less
                grid_specs[x1][y1] = {'title': title}
        if type_chart == 'pie':
            grid_specs[x1][y1]['type'] = 'domain'
        if type_chart == 'treemap':
            grid_specs[x1][y1]['type'] = 'treemap'
        obj_grid[obj['name']] = (x1+1,y1+1)
    return grid_specs, obj_grid