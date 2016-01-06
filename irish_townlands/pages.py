# encoding: utf-8
"""
Simple, non-DB, flatpage like feature
"""
from django.utils.translation import ugettext as _
PAGES = {
    'about': {
        'title': _('About Townlands.ie'),
        'body': _('About'),
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
        'title': _('Copyright of Townlands.ie'),

        'body': """
            <p>"""+_("""Since this is derived from <a href="openstreetmap.org">OpenStreetMap</a> data, it's under the same licence as that. Namely the <a href="http://opendatacommons.org/licenses/odbl/">Open Data Commons Open Database License (ODbL)</a>.""")+"""</p>
            <p>"""+_("""Consult the <a href="http://www.openstreetmap.org/copyright">OpenStreetMap Copyright</a> guide for more informatiom.""")+"""</p>
        """,
    },

    'download': {
        'title': _('Downloading Townlands.ie data'),
        'body': ( """
            <div class="alert alert-warning">
                """+_("""Warning! This data is <strong>incomplete</strong> and does not cover all of Ireland. Some counties are fully mapped, others aren't finished. Coverage is being improved on a daily basis. Please consult the <a href="/progress/">progress report</a> to find out more.""")+"""
            </div>
            <p>"""+_("The data from Townlands.ie is available in many formats")+"""</p>
            <table class="table">
                <tr>
                    <th>"""+_("""Type of Data""")+"""</th>
                    <th>"""+_("""Shapefile""")+"""</th>
                    <th>"""+_("""GeoJSON""")+"""</th>
                    <th>"""+_("""KML""")+"""</th>
                    <th>"""+_("""CSV""")+"""</th>
                    <th>"""+_("""no-geom CSV""")+"""</th>
                </tr>
                <tr>
                    <td>"""+_("""Townlands""")+"""</td>
                    <td><a href="/static/downloads/townlands.zip">"""+_("""download shapefile""")+"""</a></td>
                    <td><a href="/static/downloads/townlands.geojson.zip">"""+_("""download GeoJSON""")+"""</a></td>
                    <td><a href="/static/downloads/townlands.kmz">"""+_("""download KML""")+"""</a></td>
                    <td><a href="/static/downloads/townlands.csv.zip">"""+_("""download CSV""")+"""</a></td>
                    <td><a href="/static/downloads/townlands-no-geom.csv.zip">"""+_("""download no-geom CSV""")+"""</a></td>
                </tr>
                <tr>
                    <td>"""+_("""Electoral Divisions""")+"""</td>
                    <td><a href="/static/downloads/eds.zip">"""+_("""download shapefile""")+"""</a></td>
                    <td><a href="/static/downloads/eds.geojson.zip">"""+_("""download GeoJSON""")+"""</a></td>
                    <td><a href="/static/downloads/eds.kmz">"""+_("""download KML""")+"""</a></td>
                    <td><a href="/static/downloads/eds.csv.zip">"""+_("""download CSV""")+"""</a></td>
                    <td><a href="/static/downloads/eds-no-geom.csv.zip">"""+_("""download no-geom CSV""")+"""</a></td>
                </tr>
                <tr>
                    <td>"""+_("""Civil Parishes""")+"""</td>
                    <td><a href="/static/downloads/civil_parishes.zip">"""+_("""download shapefile""")+"""</a></td>
                    <td><a href="/static/downloads/civil_parishes.geojson.zip">"""+_("""download GeoJSON""")+"""</a></td>
                    <td><a href="/static/downloads/civil_parishes.kmz">"""+_("""download KML""")+"""</a></td>
                    <td><a href="/static/downloads/civil_parishes.csv.zip">"""+_("""download CSV""")+"""</a></td>
                    <td><a href="/static/downloads/civil_parishes-no-geom.csv.zip">"""+_("""download no-geom CSV""")+"""</a></td>
                </tr>
                <tr>
                    <td>"""+_("""Baronies""")+"""</td>
                    <td><a href="/static/downloads/baronies.zip">"""+_("""download shapefile""")+"""</a></td>
                    <td><a href="/static/downloads/baronies.geojson.zip">"""+_("""download GeoJSON""")+"""</a></td>
                    <td><a href="/static/downloads/baronies.kmz">"""+_("""download KML""")+"""</a></td>
                    <td><a href="/static/downloads/baronies.csv.zip">"""+_("""download CSV""")+"""</a></td>
                    <td><a href="/static/downloads/baronies-no-geom.csv.zip">"""+_("""download no-geom CSV""")+"""</a></td>
                </tr>
                <tr>
                    <td>"""+_("""Counties""")+"""</td>
                    <td><a href="/static/downloads/counties.zip">"""+_("""download shapefile""")+"""</a></td>
                    <td><a href="/static/downloads/counties.geojson.zip">"""+_("""download GeoJSON""")+"""</a></td>
                    <td><a href="/static/downloads/counties.kmz">"""+_("""download KML""")+"""</a></td>
                    <td><a href="/static/downloads/counties.csv.zip">"""+_("""download CSV""")+"""</a></td>
                    <td><a href="/static/downloads/counties-no-geom.csv.zip">"""+_("""download no-geom CSV""")+"""</a></td>
                </tr>
                <tr>
                    <td>"""+_("""Townland Touch""")+"""</td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td><a href="/static/downloads/townlandtouch.csv.zip">"""+_("""download no-geom CSV""")+"""</a></td>
                </tr>
            </table>

            <h2>"""+_("""Data format""")+"""</h2>
            <p>"""+_("""The geometry is available in <a href="spatialreference.org/ref/epsg/wgs-84/">WSG 84 (aka EPSG 4326, aka "latitude and longitude")</a> projection system.""")+"""</p>

            <h3>"""+_("""Attributes""")+"""</h3>
            <p>"""+_("""There are several columns per entry:""")+"""
                <dl class="dl-horizontal">
                    <dt>OSM_ID<dt>
                    <dd>"""+_("""Integer. The id of the object in the OSM database. If it's positive, it's a way; if it's negative, it's a relation. (Consult the <a href="http://wiki.openstreetmap.org/wiki/Elements">OSM data model</a> for more information). IDs are not shared across objects (e.g. there will never be an ED and a townland with the same OSM_ID).""")+"""</dd>
                    <dt>NAME<dt>
                    <dd>"""+_("""String. The name of the object. Should be the "common name". Almost certainly in English, but may be in Irish.""")+""" <i>("""+_("""NB: In the KML/KMZ file, this is NAME2 due to how ogr2ogr converts things. Suggestions welcome for how to fix this.""")+""")</i></dd>
                    <dt>NAME_GA<dt>
                    <dd>"""+_("""String. The name of the object in Irish.""")+"""</dd>
                    <dt>NAME_EN<dt>
                    <dd>"""+_("""String. The name of the object in English. Many objects don't have this, in which case presume that NAME is the English name""")+"""</dd>
                    <dt>ALT_NAME<dt>
                    <dd>"""+_("""String. Alternative name.""")+"""</dd>
                    <dt>ALT_NAME_G<dt>
                    <dd>"""+_("""String. Alternative Irish name. (it's short for "alt_name:ga")""")+"""</dd>
                    <dt>AREA<dt>
                    <dd>"""+_("""Float. Area in square metres""")+"""</dd>
                    <dt>LATITUDE<dt>
                    <dd>"""+_("""Float. Latitude of the centre of this area""")+"""</dd>
                    <dt>LONGITUDE<dt>
                    <dd>"""+_("""Float. Longitude of the centre of this area.""")+"""</dd>
                    <dt>OSM_USER<dt>
                    <dd>"""+_("""String. Username of the OSM user who mapped this""")+"""</dd>
                    <dt>OSM_TIMEST<dt>
                    <dd>"""+_("""String. ISO formatted datetime of when the object was added to OSM""")+"""</dd>
                    <dt>epoch_tstmp<dt>
                    <dd>"""+_("""Integer. <a href="https://en.wikipedia.org/wiki/Unix_time">Unix 'epoch' time</a> of when the object was added to OSM.""")+"""</dd>
                    <dt>t_ie_url<dt>
                    <dd>"""+_("""String. URL of this object on <a href="www.townlands.ie">Townlands.ie</a> (this site)""")+"""</dd>
                    <dt>co_name<dt>
                    <dd>"""+_("""String. Name of the county this object is in, if known. Not in 'county' or 'civil_parish' files.""")+"""</dd>
                    <dt>co_osm_id<dt>
                    <dd>"""+_("""Integer. OSM_ID of the county this object is in, if known. Not in 'county' or 'civil_parish' files.""")+"""</dd>
                    <dt>co_names<dt>
                    <dd>"""+_("""String. Comma separated list of names of the counties this object is in, if known. Orderd by the county's osm_id. Only in the 'civil_parish' files.""")+"""</dd>
                    <dt>co_osm_ids<dt>
                    <dd>"""+_("""String. Comma separated list of osm_ids of the counties this object is in, if known. Orderd by the county's osm_id. Only in the 'civil_parish' files.""")+"""</dd>
                    <dt>ed_name<dt>
                    <dd>"""+_("""String. Name of the ED this object is in, if known. Only in 'townland' files.""")+"""</dd>
                    <dt>ed_osm_id<dt>
                    <dd>"""+_("""Integer. OSM_ID of the ED this object is in, if known. Only in 'townland' files.""")+"""</dd>
                    <dt>cp_name<dt>
                    <dd>"""+_("""String. Name of the civil parish this object is in, if known. Only in 'townland' files.""")+"""</dd>
                    <dt>cp_osm_id<dt>
                    <dd>"""+_("""Integer. OSM_ID of the civil parish this object is in, if known. Only in 'townland' files.""")+"""</dd>
                    <dt>bar_name<dt>
                    <dd>"""+_("""String. Name of the barony this object is in, if known. Only in 'townland' files.""")+"""</dd>
                    <dt>bar_osm_id<dt>
                    <dd>"""+_("""Integer. OSM_ID of the barony this object is in, if known. Only in 'townland' files.""")+"""</dd>
                    <dt>attributio<dt>
                    <dd>"""+_("""String. Value of the 'attribution' tag (if any)""")+"""</dd>
                </dl>
            </p>

            <h3>"""+_("""Geom and no-geom version""")+"""</h3>
            <p>"""+_("""There are two CSV files, a normal version, and a "no-geom" version. The normal CSV file has an additional column:""")+"""
                <dl class="dl-horizontal">
                    <dt>WKT</dt>
                    <dd>"""+_("""String. <a href="//en.wikipedia.org/wiki/Well-known_text">Well-known text</a> representation of this area.""")+"""</dd>
                </dl>
                """+_("""The "no-geom" CSV file does not have this, and has no geometry shape data at all (it only has the LATITUDE and LONGITUDE fields). This file is suitable if you want to do some analysis on the data in a spreadsheet programme. Some spreadsheets have trouble with the long WKT field in the regular CSV version.""")+"""
            </p>
            
            <h3>"""+_("""Townland Touch""")+"""</h3>
            <p>"""+_("""When we sync from OpenStreetMap, we calculate what townlands touch each other, and how (north/south/east/west). This allows us to have a "This townland borders the follow townlands:..." feature. The "Townland Touch" dataset contains a CSV export of this data. It has the following fields:""")+"""
                <dl class="dl-horizontal">
                    <dt>t1_osm_id</dt>
                    <dd>"""+_("""osm_id of townland 1""")+"""</dd>
                    <dt>t2_osm_id</dt>
                    <dd>"""+_("""osm_id of townland 2""")+"""</dd>
                    <dt>direction</dt>
                    <dd>"""+_("""Rough direction, in degrees, in which these 2 townlands border, as seen from t1. 0 = north, 90 = east etc.""")+"""</dd>
                    <dt>lenght_m</dt>
                    <dd>"""+_("""The length, in metres, of the shared border.""")+"""</dd>
                </dl>
                """+_("""For every two townlands (A & B) that touch, there will be 2 rows in this file. One where A is townland 1, the other were B is townland 1.""")+"""
            </p>


            <h2>"""+_("""Copyright & Licence""")+"""</h2>
            <p>"""+_("""Since this is derived from <a href="openstreetmap.org">OpenStreetMap</a> data, it's under the same licence as that. Namely the <a href="http://opendatacommons.org/licenses/odbl/">Open Data Commons Open Database License (ODbL)</a>.""")+"""</p>
            <p>"""+_("""Consult the <a href="http://www.openstreetmap.org/copyright">OpenStreetMap Copyright</a> guide for more information.""")+"""</p>

        """, )
    },

    'data_freshness': {
        'title': _("How up-to-date is Townlands.ie?"),
        'body': """
            <p>"""+_("""Townlands.ie is updated every day. At the bottom of the page, you can see the date and time of the last import of data.""")+"""</p>
            <p>"""+_("""We use the Ireland extracts from <a href="http://planet.openstreetmap.ie/">OSM Data for Ireland</a>.""")+"""</p>
        """,
    },
    '25k-townlands': {
        'title': _('25,000 Townlands!'),
        'body': """
        <h2>"""+_("""25,000 Townlands""")+"""</h2>
        <p>"""+_("""The Irish OpenStreetMap community has now passed an impressive milestone. 25,000 townlands have now been mapped and added to OSM!""")+"""</p>

        <p>"""+_("""The 25,000th townland was added by <a href="/mapper/NoelB">NoelB</a>. On the 29th March 2015, they uploaded 3 townlands, one of which was the magic 25,000, <a href="/roscommon/corlis/">Corlis, Co. Roscommon</a>.""")+"""

        <h2>"""+_("""What are townlands?""")+"""</h2>
        <p>"""+_("""A townland is a small geographical division of land. The townland system is of Gaelic origin, pre-dating the Norman invasion, and most have names of Irish origin. However, some townland names and boundaries come from Norman manors, <a href="https://en.wikipedia.org/wiki/Plantations_of_Ireland">plantation divisions</a>, or later creations of the <a href="https://fr.wikipedia.org/wiki/Ordnance_Survey">Ordnance Survey</a>.""")+"""</p>

        <p>"""+_("""There are approx. 61,000 townlands in Ireland according to Wikipedia. Through a donation of out of copyright sheets from Trinity College Dublin, the Irish OpenStreetMap community now has a source from which to map all townlands on the island of Ireland.""")+"""</p>
        <h3>"""+_("""Why are they important to have?""")+"""</h3>
        <p>"""+_("""In Ireland, a townland is (generally) the smallest administrative division of land and they form the building blocks for higher-level administrative units such as: Civil Parishes, Electoral Divisions (in the Republic of Ireland) or Wards (in Northern Ireland), Baronies, Counties (will allow for accurate fine tuning of pre-existing data in OSM), Provinces (will allow for accurate fine tuning of pre-existing data in OSM), Local, National & European Election Constituencies,""")+""" 
        <p>"""+_("""The benefits of having all townland boundaries mapped in OpenStreetMap are:""")+"""</p>
        <ul>
            <li>"""+_("""It will allow for geocoding of rural addresses""")+"""</li>
            <li>"""+_("""It will enable anyone to fully utilize and visualize Census data""")+"""</li>
            <li>"""+_("""Highly useful for genealogical searches for people looking into the history of family trees of immigrants down the centuries""")+"""</li>
            <li>"""+_("""Gives the option of using OSM data for a much higher level of statistical analysis as presently the smallest boundaries available with which to divide up Ireland are City & County boundaries.""")+"""</li>
            <li>"""+_("""All of the above plus the favourable terms of the ODbL license applies ensuring this data is free to use for any and all that want to make use of it, in other words, no exorbitant fee's would apply for this data.""")+"""</li>
        </ul>

        <h2>"""+_("""About the Townland mapping project""")+"""</h2>
        <p>"""+_("""Each townland has had to be manually traced and added to OSM. Our mappers have been working on the problem for years. We're <a href="/progress/">currently only 42%% of the way through</a>, so it'll be another year before we're finished. We're adding about 100 per day <a href="/progress/activity/">at this rate</a>.""")+"""</p>

        <p><a href="http://wiki.openstreetmap.org/wiki/Ireland/Mapping_Townlands">"""+_("""How to map townlands""")+"""</a>.</p>

        
        """,
    },
    'maps': {
        'title': _('Townlands.ie Maps'),
        'body': """
        <p>Townlands.ie provides several maps based on townlands.</p>
        <h2>When were townlands mapped</h2>
        <div id="townlandage" data-mapurl="http://www.townlands.ie/tiles/townlandage/{z}/{x}/{y}.png" class="map" style="width:100%; height:700px;"></div>
        <p>Legend:
            <span style="width: 10px; height: 10px; background-color: #9e0142; display: inline-block"> </span> Today or Yesterday
            <span style="width: 10px; height: 10px; background-color: #d53e4f; display: inline-block"> </span> Last 3 days
            <span style="width: 10px; height: 10px; background-color: #f46d43; display: inline-block"> </span> Last 4 days
            <span style="width: 10px; height: 10px; background-color: #fdae61; display: inline-block"> </span> Last 5 days
            <span style="width: 10px; height: 10px; background-color: #fee08b; display: inline-block"> </span> Last 6 days
            <span style="width: 10px; height: 10px; background-color: #e6f598; display: inline-block"> </span> Last 7 days
            <span style="width: 10px; height: 10px; background-color: #abdda4; display: inline-block"> </span> Last 30 days
            <span style="width: 10px; height: 10px; background-color: #66c2a5; display: inline-block"> </span> Last 6 months
            <span style="width: 10px; height: 10px; background-color: #5e4fa2; display: inline-block"> </span> Older
        </p>

        <h2>Who has mapped townlands</h2>
        <div id="townlanduser" data-mapurl="http://www.townlands.ie/tiles/townlanduser/{z}/{x}/{y}.png" class="map" style="width:100%; height:700px;"></div>

        <h2>Land not in any county</h2>
        <div id="townlanduser" data-mapurl="http://www.townlands.ie/tiles/not_counties/{z}/{x}/{y}.png" class="map" style="width:100%; height:700px;"></div>

        <script>
            $(document).ready(function() {
                $(".map").each(function() {
                    // create the map
                    var map = new L.Map($(this).attr('id'));
                    var osmUrl='http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
                    var osmAttrib='Map data © OpenStreetMap contributors';
                    var osm = new L.TileLayer(osmUrl, {minZoom: 5, maxZoom: 18, attribution: osmAttrib});
                    var mapurl = $(this).data("mapurl");
                    var layer = new L.TileLayer(mapurl, {minZoom: 0, maxZoom: 18, attribution: osmAttrib});

                    map.setView(new L.LatLng( 53.4357, -7.7124), 7 );
                    map.addLayer(osm);
                    map.addLayer(layer);

                    // Add the 'open in JOSM button'
                    var button = $("<button>", {
                        class:"btn btn-primary",
                        html: "Open in JOSM",
                    }).on("click", function() {
                        var bounds = map.getBounds();
                        var left = bounds.getWest();
                        var right = bounds.getEast();
                        var top = bounds.getNorth();
                        var bottom = bounds.getSouth();
                        jQuery.get("http://localhost:8111/load_and_zoom?left="+left+"&right="+right+"&bottom="+bottom+"&top="+top);
                    });
                    $(this).after(button);


                });
            });
        </script>
        """,
    },
}
