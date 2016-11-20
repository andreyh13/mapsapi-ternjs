Google Maps JavaScript API v3 JSON description
==============================================

## Description

This project generates [JSON type description](http://ternjs.net/doc/manual.html#typedef) file for Google Maps JavaScript API v3.
This file can be loaded by [TernJs](http://ternjs.net/) that allows to have code hints in IDEs that use TernJs as code-analysis engine for JavaScript.

## How to use

### Brackets

- Copy googlemapsjsv3.json to your project folder.

- Add it in libs section of .tern-project file

For example,

    {
        "libs": [
            "{ternific}/libs/tern/defs/reserved",
            "{ternific}/libs/tern/defs/lodash",
            "ecma5",
            "browser",
            "jquery",
            "{project}/googlemapsjsv3"
        ],
        "loadEagerly": [],
        "async": true,
        "plugins": {
            "es_modules": true
        }
    }

For more details please refer TernJs [documentation](http://ternjs.net/doc/manual.html#plugin_third_party)    
