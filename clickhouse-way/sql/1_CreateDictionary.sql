CREATE DICTIONARY regexp_dict_api
(
    regexp      String,
    tag         String,
    method      String,
    blacklisted String,
    description String
)
    PRIMARY KEY (regexp)
SOURCE(YAMLRegExpTree (PATH '/var/lib/clickhouse/user_files/regexp_dictionary.yaml'))
LAYOUT(regexp_tree)
lifetime(0);