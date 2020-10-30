from tqdm import tqdm

class Task():
    '''Object for initializing progress bar for downloads and performing
    the download upon call
    '''
    def __init__(self, vid, quality):
        self.vid = vid
        self.path = vid.course.dir_path()
        self.url = vid.url(quality)
        self.length = vid.get_content_len(quality)
        text = 'lec{}.mp4'.format(str(vid.index).zfill(2))
        self.pbar = tqdm(
            total=int(int(self.length)/8192), initial=0, position=vid.index,
            desc=text, leave=False, ncols=90,
            bar_format='{desc} {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}')
        self.pbar.update(0)

    # <Task> --------------------------------------------------------------- //
    def finish_msg(self):
        '''Display confirmation message'''
        self.pbar.display(msg='{} downloaded.'.format(self.vid.vid_title()),
                          pos=self.vid.index)

    # <Task> --------------------------------------------------------------- //
    def download(self):
        '''Stream downloads file pointed to by self.url and returns index'''
        with self.vid.course.get_driver().request('GET', self.url, stream=True) as res:
            res.raise_for_status()

            with open('{}/{}.mp4'.format(self.path, self.vid.vid_title()), 'wb') as file:
                for chunk in res.iter_content(chunk_size=8192):
                    self.pbar.update(1)
                    file.write(chunk)
                self.finish_msg()
            #self.pbar.close()
