ValueError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/streamlit_app/youtube/app.py", line 151, in <module>
    ax.imshow(wordcloud, interpolation='interlink')
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/matplotlib/__init__.py", line 1528, in inner
    return func(
        ax,
        *map(cbook.sanitize_sequence, args),
        **{k: cbook.sanitize_sequence(v) for k, v in kwargs.items()})
File "/home/adminuser/venv/lib/python3.14/site-packages/matplotlib/axes/_axes.py", line 6363, in imshow
    im = mimage.AxesImage(self, cmap=cmap, norm=norm, colorizer=colorizer,
                          interpolation=interpolation, origin=origin,
    ...<2 lines>...
                          interpolation_stage=interpolation_stage,
                          **kwargs)
File "/home/adminuser/venv/lib/python3.14/site-packages/matplotlib/image.py", line 908, in __init__
    super().__init__(
    ~~~~~~~~~~~~~~~~^
        ax,
        ^^^
    ...<9 lines>...
        **kwargs
        ^^^^^^^^
    )
    ^
File "/home/adminuser/venv/lib/python3.14/site-packages/matplotlib/image.py", line 283, in __init__
    self.set_interpolation(interpolation)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/matplotlib/image.py", line 752, in set_interpolation
    _api.check_in_list(interpolations_names, interpolation=s)
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/matplotlib/_api/__init__.py", line 227, in check_in_list
    raise ValueError(list_suggestion_error_msg(key, val, values))
