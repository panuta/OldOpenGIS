var opengis = function(type) {
    this.idText = '';
    this.idMap = '';
    this.map = null;
    this.controls = null;
    this.panel = null;
    this.layers = {};
    this.re = new RegExp("^SRID=\d+;(.+)", "i");
    this.wkt_f = new OpenLayers.Format.WKT();
    
    this.init = function(type) {
        // If not set type is polygon.
        if (type == 'polygon') {
            this.is_collection = true;
            this.collection_type = 'Polygon';
            this.is_linestring = false;
            this.is_polygon = true;
            this.is_point = false;
        }
        else if (type == 'point'){
            this.is_collection = false;
            this.collection_type = 'None';
            this.is_linestring = false;
            this.is_polygon = false;
            this.is_point = true;
        }
    };
    
    this.get_ewkt = function(feat) {
        return this.wkt_f.write(feat);
    };
    
    this.read_wkt = function(wkt) {
        // OpenLayers cannot handle EWKT -- we make sure to strip it out.
        // EWKT is only exposed to OL if there's a validation error in the admin.
        var match = this.re.exec(wkt);
        if (match) {
            wkt = match[1];
        }
        
        return this.wkt_f.read(wkt);
    };
    
    this.write_wkt = function(feat) {
        if (this.is_collection) {
            this.num_geom = feat.geometry.components.length;
        }
        else {
            this.num_geom = 1;
        }
        document.getElementById(this.idText).value = this.get_ewkt(feat);
    };
    
    this.add_wkt = function(event) {
        // This function will sync the contents of the `vector` layer with the
        // WKT in the text field.
        
        if (this.is_collection) {
            var feat = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.MultiPolygon());
            for (var i = 0; i < this.layers.vector.features.length; i++) {
                feat.geometry.addComponents([this.layers.vector.features[i].geometry]);
            }
            this.write_wkt(feat);
        } else {
            // Make sure to remove any previously added features.

            if (this.layers.vector.features.length > 1) {
                old_feats = [this.layers.vector.features[0]];
                this.layers.vector.removeFeatures(old_feats);
                this.layers.vector.destroyFeatures(old_feats);
            }

            this.write_wkt(event.feature);
        }
    };
    
    this.modify_wkt = function(event) {
        if (this.is_collection) {
            if (this.is_point) {
                this.add_wkt(event);
                return;
            } else {
                // When modifying the selected components are added to the
                // vector layer so we only increment to the `num_geom` value.
                var feat = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.MultiPolygon());
                for (var i = 0; i < this.num_geom; i++) {
                    feat.geometry.addComponents([this.layers.vector.features[i].geometry]);
                }
                this.write_wkt(feat);
            }
        } else {
            this.write_wkt(event.feature);
        }
    };
    
    // Function to clear vector features and purge wkt from div
    this.deleteFeatures = function() {
        this.layers.vector.removeFeatures(this.layers.vector.features);
        this.layers.vector.destroyFeatures();
    };
    
    this.clearFeatures = function() {
        this.deleteFeatures();
        document.getElementById(this.idText).value = '';
        this.map.setCenter(new OpenLayers.LonLat(0, 0), 4);
    };
    
    // Add Select control
    this.addSelectControl = function() {
        var select = new OpenLayers.Control.SelectFeature(this.layers.vector, {
            'toggle': true,
            'clickout': true
        });
        this.map.addControl(select);
        select.activate();
    };
    
    this.enableDrawing = function() {
        this.map.getControlsByClass('OpenLayers.Control.DrawFeature')[0].activate();
    };
    
    this.enableEditing = function() {
        this.map.getControlsByClass('OpenLayers.Control.ModifyFeature')[0].activate();
    };

    // Create an array of controls based on geometry type
    this.getControls = function(lyr) {
        this.panel = new OpenLayers.Control.Panel({
            'displayClass': 'olControlEditingToolbar'
        });
        var nav = new OpenLayers.Control.Navigation();
        var draw_ctl;
        if (this.is_linestring) {
            draw_ctl = new OpenLayers.Control.DrawFeature(lyr, OpenLayers.Handler.Path, {
                'displayClass': 'olControlDrawFeaturePath'
            });
        } else if (this.is_polygon) {
            draw_ctl = new OpenLayers.Control.DrawFeature(lyr, OpenLayers.Handler.Polygon, {
                'displayClass': 'olControlDrawFeaturePolygon'
            });
        } else if (this.is_point) {
            draw_ctl = new OpenLayers.Control.DrawFeature(lyr, OpenLayers.Handler.Point, {
                'displayClass': 'olControlDrawFeaturePoint'
            });
        }

        var mod = new OpenLayers.Control.ModifyFeature(lyr, {
            'displayClass': 'olControlModifyFeature'
        });
        this.controls = [nav, draw_ctl, mod];

    };
    
    this.geoField = function(idText, idMap) {
        this.idText = idText;
        this.idMap = idMap;
        
        // The options hash, w/ zoom, resolution, and projection settings.
        var options = {
            'projection': new OpenLayers.Projection("EPSG:4326"),
            'numZoomLevels': 18
        };
        // The admin map for this geometry field.
        this.map = new OpenLayers.Map(this.idMap, options);
        // Base Layer
        this.layers.base = new OpenLayers.Layer.WMS("OpenLayers WMS", "http://labs.metacarta.com/wms/vmap0", {
            layers: 'basic'
        });
        this.map.addLayer(this.layers.base);


        this.layers.vector = new OpenLayers.Layer.Vector(this.idMap);
        this.map.addLayer(this.layers.vector);
        // Read WKT from the text field.
        var wkt = document.getElementById(this.idText).value;
        if (wkt) {
            // After reading into geometry, immediately write back to
            // WKT <textarea> as EWKT (so that SRID is included).
            var admin_geom = this.read_wkt(wkt);
            this.write_wkt(admin_geom);
            if (this.is_collection) {
                // If geometry collection, add each component individually so they may be
                // edited individually.
                for (var i = 0; i < this.num_geom; i++) {
                    this.layers.vector.addFeatures([new OpenLayers.Feature.Vector(admin_geom.geometry.components[i].clone())]);
                }
            } else {
                this.layers.vector.addFeatures([admin_geom]);
            }
            // Zooming to the bounds.
            this.map.zoomToExtent(admin_geom.geometry.getBounds());
            if (this.is_point) {
                this.map.zoomTo(12);
            }
        } else {
            this.map.setCenter(new OpenLayers.LonLat(0, 0), 4);
        }
        // This allows editing of the geographic fields -- the modified WKT is
        // written back to the content field (as EWKT, so that the ORM will know
        // to transform back to original SRID).
        this.layers.vector.events.on({
            "featuremodified": this.modify_wkt,
            "scope": this
        });
        
        this.layers.vector.events.on({
            "featureadded": this.add_wkt,
            "scope": this
        });



        // Map controls:
        // Add geometry specific panel of toolbar controls
        this.getControls(this.layers.vector);
        this.panel.addControls(this.controls);
        this.map.addControl(this.panel);
        this.addSelectControl();
        // Then add optional visual controls
        this.map.addControl(new OpenLayers.Control.MousePosition());
        this.map.addControl(new OpenLayers.Control.Scale());
        this.map.addControl(new OpenLayers.Control.LayerSwitcher());
        // Then add optional behavior controls

        if (wkt) {
            this.enableEditing();
            this.enableDrawing();
        } else {
            this.enableDrawing();
        }
    }
    
    
    this.init(type);
    
};

