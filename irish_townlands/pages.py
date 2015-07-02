"""
Simple, non-DB, flatpage like feature
"""
PAGES = {
    'about': {
        'title': 'About Townlands.ie',
        'body': 'About',
    },
    
    'news': {
        'title': 'News',
        'body': """
        <h2>News from the Townlands Mapping Project</h2>
        <ul>
            <li>31st March 2015 - <a href="/page/25k-townlands/">25,000 Townlands have been mapped</a></li>
        </ul>
        """,
    },

    'copyright': {
        'title': 'Copyright of Townlands.ie',

        'body': """
            <p>Since this is derived from <a href="openstreetmap.org">OpenStreetMap</a> data, it's under the same licence as that. Namely the <a href="http://opendatacommons.org/licenses/odbl/">Open Data Commons Open Database License (ODbL)</a>.</p>
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
                <tr>
                    <td>Townland Touching</td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td><a href="/static/downloads/townlandtouch.csv.zip">download no-geom CSV</a></td>
                </tr>
            </table>

            <h2>Data format</h2>
            <p>The geometry is available in <a href="spatialreference.org/ref/epsg/wgs-84/">WSG 84 (aka EPSG 4326, aka "latitude and longitude")</a> projection system.</p>

            <h3>Attributes</h3>
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
                    <dd>Integer. OSM_ID of the county this object is in, if known. Not in 'county' files.</dd>
                    <dt>ed_name<dt>
                    <dd>String. Name of the ED this object is in, if known. Only in 'townland' files.</dd>
                    <dt>ed_osm_id<dt>
                    <dd>Integer. OSM_ID of the ED this object is in, if known. Only in 'townland' files.</dd>
                    <dt>cp_name<dt>
                    <dd>String. Name of the civil parish this object is in, if known. Only in 'townland' files.</dd>
                    <dt>cp_osm_id<dt>
                    <dd>Integer. OSM_ID of the civil parish this object is in, if known. Only in 'townland' files.</dd>
                    <dt>bar_name<dt>
                    <dd>String. Name of the barony this object is in, if known. Only in 'townland' files.</dd>
                    <dt>bar_osm_id<dt>
                    <dd>Integer. OSM_ID of the barony this object is in, if known. Only in 'townland' files.</dd>
                    <dt>attributio<dt>
                    <dd>String. Value of the 'attribution' tag (if any)</dd>
                </dl>
            </p>

            <h3>Geom and no-geom version</h3>
            <p>There are 2 CSV files, a normal version, and a "no-geom" version. The CSV file has an additional column:
                <dl class="dl-horizontal">
                    <dt>WKT</dt>
                    <dd>String. <a href="//en.wikipedia.org/wiki/Well-known_text">Well-known text</a> representation of this area.</dd>
                </dl>
                The "no-geom" CSV file does not have this, and has no geometry shape data at all (it only has the LATITUDE and LONGITUDE fields). This file is suitable if you want to do some analysis on the data in a spreadsheet programme. Some spreadsheets have trouble with the long WKT field in the regular CSV version.
            </p>
            
            <h3>Townland Touch</h3>
            <p>When we sync from OpenStreetMap, we calculate what townlands touch each other, and how (north/south/east/west). This allows us to have a "This townland borders the follow townlands:..." feature. The "Townland Touch" dataset contains a CSV export of this data. It has the following fields:
                <dl class="dl-horizontal">
                    <dt>t1_osm_id</dt>
                    <dd>osm_id of townland 1</dd>
                    <dt>t2_osm_id</dt>
                    <dd>osm_id of townland 2</dd>
                    <dt>direction</dt>
                    <dd>Rough direction, in degrees, in which these 2 townlands border, as seen from t1. 0 = north, 90 = east etc.</dd>
                    <dt>lenght_m</dt>
                    <dd>The length, in metres, of the shared border.</dd>
                </dl>
                For every two townlands (A & B) that touch, there will be 2 rows in this file. One where A is townland 1, the other were B is townland 1.
            </p>


            <h2>Copyright & Licence</h2>
            <p>Since this is derived from <a href="openstreetmap.org">OpenStreetMap</a> data, it's under the same licence as that. Namely the <a href="http://opendatacommons.org/licenses/odbl/">Open Data Commons Open Database License (ODbL)</a>.</p>
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
    '25k-townlands': {
        'title': '25,000 Townlands!',
        'body': """
        <h2>25,000 Townlands</h2>
        <p>The Irish OpenStreetMap community has now passed an impressive milestone. 25,000 townlands have now been mapped and added to OSM!</p>

        <p>The 25,000th townland was added by <a href="/mapper/NoelB">NoelB</a>. On the 29th March 2015, they uploaded 3 townlands, one of which was the magic 25,000, <a href="/roscommon/corlis/">Corlis, Co. Roscommon</a>.

        <h2>What are townlands?</h2>
        <p>A townland is a small geographical division of land. The townland system is of Gaelic origin, pre-dating the Norman invasion, and most have names of Irish origin. However, some townland names and boundaries come from Norman manors, plantation divisions, or later creations of the Ordnance Survey.</p>

        <p>There are approx. 61,000 townlands in Ireland according to Wikipedia. Through a donation of out of copyright sheets from Trinity College Dublin, the Irish OpenStreetMap community now has a source from which to map all townlands on the island of Ireland.</p>
        <h3>Why are they important to have?</h3>
        <p>In Ireland, a townland is (generally) the smallest administrative division of land and they form the building blocks for higher-level administrative units such as: Civil Parishes, Electoral Divisions (in the Republic of Ireland) or Wards (in Northern Ireland), Baronies, Counties (will allow for accurate fine tuning of pre-existing data in OSM), Provinces (will allow for accurate fine tuning of pre-existing data in OSM), Local, National & European Election Constituencies, 
        <p>The benefits of having all townland boundaries mapped in OpenStreetMap are:</p>
        <ul>
            <li> It will allow for geocoding of rural addresses</li>
            <li>It will enable anyone to fully utilize and visualize Census data</li>
            <li>Highly useful for genealogical searches for people looking into the history of family trees of immigrants down the centuries</li>
            <li>Gives the option of using OSM data for a much higher level of statistical analysis as presently the smallest boundaries available with which to divide up Ireland are City & County boundaries.</li>
            <li>All of the above plus the favourable terms of the ODbL license applies ensuring this data is free to use for any and all that want to make use of it, in other words, no exorbitant fee's would apply for this data.</li>
        </ul>

        <h2>About the Townland mapping project</h2>
        <p>Each townland has had to be manually traced and added to OSM. Our mappers have been working on the problem for years. We're <a href="/progress/">currently only 42% of the way through</a>, so it'll be another year before we're finished. We're adding about 100 per day <a href="/progress/activity/">at this rate</a>.</p>

        <p><a href="http://wiki.openstreetmap.org/wiki/Ireland/Mapping_Townlands">How to map townlands</a>.</p>

        
        """,
    },


}
