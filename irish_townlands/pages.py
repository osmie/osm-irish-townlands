"""
Simple, non-DB, flatpage like feature
"""
PAGES = {
    'about': {
        'title': 'About Townlands.ie',
        'body': 'About',
    },

    'copyright': {
        'title': 'Copyright of Townlands.ie',

        'body': """
            <p>Since this is derived from <a href="openstreetmap.org">OpenStreeMap</a> data, it's under the same licence as that. Namely the <a href="http://opendatacommons.org/licenses/odbl/">Open Data Commons Open Database License (ODbL)</a>.</p>
            <p>Consult the <a href="http://www.openstreetmap.org/copyright">OpenStreetMap Copyright</a> guide for more informatiom.</p>
        """,
    },

    'download': {
        'title': 'Downloading Townlands.ie data',
        'body': """
            <div class="alert alert-warning">
                Warning! This data is <strong>incomplete</strong> and does not cover all of Ireland. Some counties are fully mapped, others aren't finished. Coverage is being improved on a daily basis. Please consult the <a href="/progress/">progress report</a> to find out more.
            </div>
            <p>The data from townlands.ie is available in many formats</p>
            <table class="table">
                <tr>
                    <th>Type of Data</th>
                    <th>Shapefile</th>
                    <th>GeoJSON</th>
                    <th>KML</th>
                    <th>CSV</th>
                </tr>
                <tr>
                    <td>Townlands</td>
                    <td><a href="/static/downloads/townlands.zip">download shapefile</a></td>
                    <td><a href="/static/downloads/townlands.geojson.zip">download GeoJSON</a></td>
                    <td><a href="/static/downloads/townlands.kmz">download KML</a></td>
                    <td><a href="/static/downloads/townlands.csv.zip">download CSV</a></td>
                    <td><a href="/static/downloads/townlands-no-geom.csv.zip">download no-geom CSV</a></td>
                </tr>
                <tr>
                    <td>Electoral Divisions</td>
                    <td><a href="/static/downloads/eds.zip">download shapefile</a></td>
                    <td><a href="/static/downloads/eds.geojson.zip">download GeoJSON</a></td>
                    <td><a href="/static/downloads/eds.kmz">download KML</a></td>
                    <td><a href="/static/downloads/eds.csv.zip">download CSV</a></td>
                    <td><a href="/static/downloads/eds-no-geom.csv.zip">download no-geom CSV</a></td>
                </tr>
                <tr>
                    <td>Civil Parishes</td>
                    <td><a href="/static/downloads/civil_parishes.zip">download shapefile</a></td>
                    <td><a href="/static/downloads/civil_parishes.geojson.zip">download GeoJSON</a></td>
                    <td><a href="/static/downloads/civil_parishes.kmz">download KML</a></td>
                    <td><a href="/static/downloads/civil_parishes.csv.zip">download CSV</a></td>
                    <td><a href="/static/downloads/civil_parishes-no-geom.csv.zip">download no-geom CSV</a></td>
                </tr>
                <tr>
                    <td>Baronies</td>
                    <td><a href="/static/downloads/baronies.zip">download shapefile</a></td>
                    <td><a href="/static/downloads/baronies.geojson.zip">download GeoJSON</a></td>
                    <td><a href="/static/downloads/baronies.kmz">download KML</a></td>
                    <td><a href="/static/downloads/baronies.csv.zip">download CSV</a></td>
                    <td><a href="/static/downloads/baronies-no-geom.csv.zip">download no-geom CSV</a></td>
                </tr>
                <tr>
                    <td>Counties</td>
                    <td><a href="/static/downloads/counties.zip">download shapefile</a></td>
                    <td><a href="/static/downloads/counties.geojson.zip">download GeoJSON</a></td>
                    <td><a href="/static/downloads/counties.kmz">download KML</a></td>
                    <td><a href="/static/downloads/counties.csv.zip">download CSV</a></td>
                    <td><a href="/static/downloads/counties-no-geom.csv.zip">download no-geom CSV</a></td>
                </tr>
            </table>

            <h2>Data format</h2>
            <p>The geometry is available in <a href="spatialreference.org/ref/epsg/wgs-84/">WSG 84 (aka EPSG 4326, aka "latitude and longitude")</a> projection system.</p>

            <p>There are several columns per entry:
                <dl class="dl-horizontal">
                    <dt>OSM_ID<dt>
                    <dd>Integer. The id of the object in the OSM database. If it's positive, it's a way; if it's negative, it's a relation. (Consult the <a href="http://wiki.openstreetmap.org/wiki/Elements">OSM data model</a> for more). IDs are not shared across objects (e.g. there will never be an ED and a townland with the same OSM_ID).</dd>
                    <dt>NAME<dt>
                    <dd>String. The name of the object. Should be the "common name". Almost certainly in English, but may be in Irish. <i>(NB: In the KML/KMZ file, this is NAME2 due to how ogr2ogr converts things. Suggestions welcome for how to fix this.)</i></dd>
                    <dt>NAME_GA<dt>
                    <dd>String. The name of the object in Irish.</dd>
                    <dt>NAME_EN<dt>
                    <dd>String. The name of the object in English. Many objects don't have this, in which case presume that NAME is the English name</dd>
                    <dt>ALT_NAME<dt>
                    <dd>String. Alternative name.</dd>
                    <dt>ALT_NAME_G<dt>
                    <dd>String. Alternative Irish name. (it's short for "alt_name:ga")</dd>
                    <dt>AREA<dt>
                    <dd>Float. Area in square metres</dd>
                    <dt>LATITUDE<dt>
                    <dd>Float. Latitude of the centre of this area</dd>
                    <dt>LONGITUDE<dt>
                    <dd>Float. Longitude of the centre of this area.</dd>
                    <dt>OSM_USER<dt>
                    <dd>String. Username of the OSM user who mapped this</dd>
                    <dt>OSM_TIMEST<dt>
                    <dd>String. ISO formatted datetime of when the object was added to OSM</dd>
                    <dt>epoch_tstmp<dt>
                    <dd>Integer. <a href="https://en.wikipedia.org/wiki/Unix_time">Unix 'epoch' time</a> of when the object was added to OSM.</dd>
                    <dt>t_ie_url<dt>
                    <dd>String. URL of this object on <a href="www.townlands.ie">Townlands.ie</a> (this site)</dd>
                    <dt>co_name<dt>
                    <dd>String. Name of the county this object is in, if known. Not in 'county' files.</dd>
                    <dt>co_osm_id<dt>
                    <dd>Intger. OSM_ID of the county this object is in, if known. Not in 'county' files.</dd>
                    <dt>ed_name<dt>
                    <dd>String. Name of the ED this object is in, if known. Only in 'townland' files.</dd>
                    <dt>ed_osm_id<dt>
                    <dd>Intger. OSM_ID of the ED this object is in, if known. Only in 'townland' files.</dd>
                    <dt>cp_name<dt>
                    <dd>String. Name of the civil parish this object is in, if known. Only in 'townland' files.</dd>
                    <dt>cp_osm_id<dt>
                    <dd>Integer. OSM_ID of the civil parish this objet is in, if known. Only in 'townland' files.</dd>
                    <dt>bar_name<dt>
                    <dd>String. Name of the barony this object is in, if known. Only in 'townland' files.</dd>
                    <dt>bar_osm_id<dt>
                    <dd>Integer. OSM_ID of the barony this object is in, if known. Only in 'townland' files.</dd>
                </dl>
            </p>

            <p>There are 2 CSV files, a normal version, and a "no-geom" version. The CSV file has an additional column:
                <dl class="dl-horizontal">
                    <dt>WKT</dt>
                    <dd>String. <a href="//en.wikipedia.org/wiki/Well-known_text">Well-known text</a> representation of this area.</dd>
                </dl>
                The "no-geom" CSV file does not have this, and has no geometry shape data at all (it only has the LATITUDE and LONGITUDE fields). This file is suitable if you want to do some analysis on the data in a spreadsheet programme. Some spreadsheets have trouble with the long WKT field in the regular CSV version.
            </p>

            <h2>Copyright & Licence</h2>
            <p>Since this is derived from <a href="openstreetmap.org">OpenStreeMap</a> data, it's under the same licence as that. Namely the <a href="http://opendatacommons.org/licenses/odbl/">Open Data Commons Open Database License (ODbL)</a>.</p>
            <p>Consult the <a href="http://www.openstreetmap.org/copyright">OpenStreetMap Copyright</a> guide for more informatiom.</p>

        """,
    },

    'data_freshness': {
        'title': "How up-to-date is Townlands.ie?",
        'body': """
            <p>Townlands.ie is updated every day. At the bottom of the page, you can see the date and time of the last import of data.</p>
            <p>We use the Ireland extracts from <a href="http://planet.openstreetmap.ie/">OSM Data for Ireland</a>.</p>
        """,
    },


}
