# click all items in a list, for btns and 'Download Original's

CLICK_ALL = '''
    function click_all(elements) {
        for (let elem of elements)
            elem.click()
    }
    '''

# extract third list item for
FILTER_LIST = '''
    function filter_list(elements) {
        let new_list = []
        for (i=0; i<elements.length; i++) {
            if (i % 3 == 2)
                new_list.push(elements[i]);
        }
        return new_list;
    }
    '''

# harvests all video links and returns array of them
OPTION_SCRAPE = '''
    function scrape_option_by_index(qual_idx) {
        vid_links = [];
        for (i=0; i<selects.length; i++) {
            vid_links.push((selects[i].options[qual_idx].value).split(' || ')[0]);
        }
        return vid_links;
    }
'''


'''
btns = document.querySelectorAll("div[class*='courseMediaIndicator capture']")
click_stuff(btns)
# wait

li_elems = document.querySelectorAll(".menu-items ul li a");
download_originals = filter_list(li_elems)


click_stuff(download_originals)
# wait

selects = document.querySelectorAll("select[name='video-one-files']")


sd = scrape_option_by_index(0)
hd = scrape_option_by_index(1)

console.log('HD: ' + hd.length + '  SD: ' + sd.length)
'''
