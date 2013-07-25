define(['jquery',
        'backbone',
        'underscore',
        'Leaflet',
        'js/models/JobModel',
        'js/models/DatafileModel',
        'text!templates/job/view_results.html',
        'text!templates/job/result_row.html',
        'json2'], 
   function ($, Backbone, _, L, JobModel, DatafileModel, 
		     ViewResultTemplate, ResultRowTemplate) {
		var JobResultsView = Backbone.View.extend({
			el: $('#job-view'),
			initialize: function() {
				_.bindAll(this, 'render', 'displayPopup');
			},
			events: {
			},
			
			displayPopup: function (feature, layer){
				layer.on('click', function (e) {
					$output=$('#result-row', this.$el);
					$('#result-div', this.$el).show();
					context={feature: feature.properties}
					var template=_.template(ResultRowTemplate, 
				                			context);
					$output.html(template);
				})
			},
			
			generateMap: function () {
				this.map=L.map('map'); 
				var that=this;
		   		var bbox=this.datafile.get("bbox")
		   		var southWest = new L.LatLng(bbox[2], bbox[0]);
		   	    var northEast = new L.LatLng(bbox[3], bbox[1]);
		   	    var bounds = new L.LatLngBounds(southWest, northEast);
		   	    var cm_url='http://{s}.tile.cloudmade.com/{key}/{styleId}/256/{z}/{x}/{y}.png'
		   	    L.tileLayer(cm_url, {
		   	    	    key: '0c9dbe8158f6482d84e3543b1a790dbb',
		   	    	    styleId: 997
		   	    }).addTo(this.map);
//		   	    L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
//		   	      attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
//		    	}).addTo(this.map);
		   		this.map.fitBounds(bounds);
		   		$.ajax({
		   			url: this.job.get("results"),
		   			dataType: "json",
		   			success: function (data) {
		   				var geojsonMarkerOptions = {
		   				    radius: 8,
		   				    fillColor: "#ff7800",
		   				    color: "#000",
		   				    weight: 1,
		   				    opacity: 1,
		   				    fillOpacity: 0.8
		   				};
		   				L.geoJson(data, {
		   				    pointToLayer: function (feature, latlng) {
		   			        	return L.circleMarker(latlng, geojsonMarkerOptions);
		   			    	},
		   			    	onEachFeature: that.displayPopup
		   				}).addTo(that.map);
		   			}
		   			
		   		});
			},
			 
			render: function (jobid) {
			   var that=this;
			   var job=new JobModel({'job_id': jobid });
			   var url="#/view/"+jobid;
			   $('#viewjob-tab').show();
			   $('#viewjob-tab').data('hide', false);
			   var $tab=$('#viewjob-tab a');  
			   if ($tab.attr("href") == url) {
				   return;
			   }
			   $tab.attr("href", url);
			   job.fetch({
				   success: function(job) {
				   		// Store the job to save time later.
				   		that.job=job;
				   		var that2=that;
				   		var data_id_parts=job.get("data_file").split('/');
				   		var data_id=data_id_parts[data_id_parts.length-2];
				   		var datafile=new DatafileModel({id: data_id})
				   		datafile.fetch({
				   			success: function (datafile) {
				   				that2.datafile=datafile;
				   				var context={'job': job,
				   						     'datafile': datafile}
						   		var template=_.template(ViewResultTemplate, 
						   				                context);
						   		that2.$el.html(template);
						   		if (job.get("status")=='Complete') {
						   			that2.generateMap()
//							   		that2.map=L.map('map'); 
//							   		var bbox=datafile.get("bbox")
//							   		var southWest = new L.LatLng(bbox[2], bbox[0]);
//							   	    var northEast = new L.LatLng(bbox[3], bbox[1]);
//							   	    var bounds = new L.LatLngBounds(southWest, northEast);
//	//						   	    var cm_url='http://{s}.tile.cloudmade.com/{key}/{styleId}/256/{z}/{x}/{y}.png'
//	//						   	    L.tileLayer(cm_url, {
//	//						   	    	    key: '0c9dbe8158f6482d84e3543b1a790dbb',
//	//						   	    	    styleId: 997
//	//						   	    }).addTo(that2.map);
//							   	    L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
//							   	      attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
//							    	}).addTo(that2.map);
//							   		that2.map.fitBounds(bounds);
//							   		$.ajax({
//							   			url: job.get("results"),
//							   			dataType: "json",
//							   			success: function (data) {
//							   				var geojsonMarkerOptions = {
//							   				    radius: 8,
//							   				    fillColor: "#ff7800",
//							   				    color: "#000",
//							   				    weight: 1,
//							   				    opacity: 1,
//							   				    fillOpacity: 0.8
//							   				};
//							   				L.geoJson(data, {
//							   				    pointToLayer: function (feature, latlng) {
//							   			        	return L.circleMarker(latlng, geojsonMarkerOptions);
//							   			    	},
//							   			    	onEachFeature: that2.displayPopup
//							   				}).addTo(that2.map);
//							   			}
//							   			
//							   		});
						   		}
				   		}
				   		});
				   		
			   	   }
			   });
			   }
		});
		return JobResultsView;	
});