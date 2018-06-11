# phBot ItemManager

this is a phBot plugin and it does:

* sort your inventory, storage and guild-storage items by `servername`

* store/take gold from storage/guild-storage in advanced mode

    * loops automatically per 1.000.000.000 gold (useful on private servers with high gold-drop-ratio)
    * use `b` or `B` for 1.000.000.000
        * example usage: `5b` = 5.000.000.000
    * use `m` or `M` for 1.000.000
    * use `k` or `K` for 1.000
    * use `0` or `all` for all available gold (currently works only with `store`)

**important**:

works only with testing release `v21.1.7` or later since `get_storage()` and `get_guild_storage()` are used and has just been implemented at this version

## installation

please refer to https://projecthax.com/showthread.php?t=14618
