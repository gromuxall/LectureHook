'''
    js.py

    Macros for javascript to be executed by Selenium WebDriver
'''

CLICK_ALL_FUNC = '''
    function click_all(elements) {
        for (let elem of elements)
            elem.click()
    }
    '''

# extract third list item for
FILTER_LIST_FUNC = '''
    function filter_list(elements) {
        let new_list = []
        for (i=0; i<elements.length; i++) {
            if (i % 3 == 2)
                new_list.push(elements[i]);
        }
        return new_list;
    }
    '''

CLICK_ALL_BTNS = '''
    btns = document.querySelectorAll("div[class*='courseMediaIndicator capture']")
    click_all(btns)
'''

CLICK_ALL_LINKS = '''
    li_elems = document.querySelectorAll(".menu-items ul li a");
    download_originals = filter_list(li_elems)
    click_all(download_originals)
'''
