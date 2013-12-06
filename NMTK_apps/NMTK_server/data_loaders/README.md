NMTK Server supports a wide range of data loaders.  These loaders all inherit
from the BaseDataLoader object and implement their own loading method(s).

In order to add new loaders, modify settings.DATA_LOADERS to contain a list
of the loaders you wish to support.  Note that you can add new loaders by
adding the loader to this directory and then adding it to the list
of DATA_LOADERS.