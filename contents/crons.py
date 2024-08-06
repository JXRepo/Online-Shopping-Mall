#######################################################################
"""
Homepage, detail page

We first query data from the database
and then render the HTML pages.

Whether it's caching data from the database or rendering HTML pages (especially category rendering, which is relatively slow),
it can affect the user experience to some extent.

The best experience is:
Users can directly access static HTML pages that have been queried from the database and rendered.

Write the HTML pages, which have been queried from the database and rendered, to the specified directory.

"""
# This function helps us query the database, render the HTML page, and then write the rendered HTML to a specified file.
import time
from utils.goods import get_categories
from apps.contents.models import ContentCategory

def generic_meiduo_index():
    print('--------------%s-------------'%time.ctime())
    # 1. Product category data
    categories = get_categories()
    # 2. Advertisement data
    contents = {}
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

    # We will discuss page staticization for our homepage later.
    # We pass the data to the template.
    context = {
        'categories': categories,
        'contents': contents,
    }

    # 1. Load the rendered template
    from django.template import loader
    index_template=loader.get_template('index.html')

    # 2. Pass the data to the template
    index_html_data=index_template.render(context)
    # 3. 把渲染好的HTML，写入到指定文件
    from meiduo_mall import settings
    import os
    # The parent directory of `base_dir`
    file_path=os.path.join(os.path.dirname(settings.BASE_DIR),'front_end_pc/index.html')

    with open(file_path,'w',encoding='utf-8') as f:
        f.write(index_html_data)



