/**
 * Select Table from Other Users Popup
 */

function show_SelectOtherUserTable_Popup(left, top, onsubmit, onclose) {
	if(!$("#select_other_user_table_popup").hasClass("initialized")) initialize_SelectOtherUserTable_Popup(onsubmit, onclose);
	$("#select_other_user_table_popup").show().css({'left':left,'top':top});
}

function initialize_SelectOtherUserTable_Popup(onsubmit, onclose) {
	$("#select_other_user_table_popup").html('<div class="close_panel"><a href="#">Close</a></div>' +
		'<h4>Choose table</h4>' + 
		'<div class="panel code-panel"><label for="id_table_code">from Table Code:</label><div class="right_panel"><input type="text" id="id_table_code" name="table_code"/> <button>Use this code</button></div></div>' + 
		'<div class="panel">or</div>' + 
		'<div class="panel username-panel"><label for="id_table_username">from Username:</label><div class="right_panel"><input type="text" id="id_table_username" name="table_username"/> <button class="load-user-tables">Load</button></div></div>' + 
		'<div class="panel loaded-username-panel" style="display:none;"><label for="id_table_username">from Username:</label><div class="right_panel"><span class="username"></span> <a href="#">Change</a><div class="tables_panel"><select name="table_list"></select><button>Use this table</button></div></div></div>');
	
	// Close popup
	$("#select_other_user_table_popup .close_panel a").click(function() {
		clear_SelectOtherUserTable_Popup();
		$("#select_other_user_table_popup").hide();
		onclose();
		return false;
	});
	
	// Select table from code
	$("#select_other_user_table_popup .code-panel button").click(function() {
		// TODO
		onsubmit("table_code", "CODE", "NAME");
	});
	
	// Load user tables
	$("#select_other_user_table_popup .username-panel button").click(function() {
		var username = $("#select_other_user_table_popup input[name='table_username']").val();
		
		if(username != "") {
			$.getJSON("/api/table/list/", {username:username}, function(data) {
				var list_html = '';
				for(var i in data.result) {
					list_html += '<option value="' + data.result[i].id + '">' + data.result[i].name + '</option>';
				}
				
				if(list_html == "") {
					list_html = "<option>No table found</option>";
					$("#select_other_user_table_popup select[name='table_list']").attr("disabled", "disabled");
					$("#select_other_user_table_popup .loaded-username-panel button").attr("disabled", "disabled");
				}
				
				$("#select_other_user_table_popup span.username").html(username);
				$("#select_other_user_table_popup select[name='table_list']").html(list_html);
				
				$("#select_other_user_table_popup .username-panel").hide();
				$("#select_other_user_table_popup .loaded-username-panel").show();
			});
		}
	});
	
	// Change username
	$("#select_other_user_table_popup .loaded-username-panel a").click(function() {
		$("#select_other_user_table_popup .username-panel input").val("");
		
		$("#select_other_user_table_popup .username-panel").show();
		$("#select_other_user_table_popup .loaded-username-panel").hide();
		
		return false;
	});
	
	// Select table from list
	$("#select_other_user_table_popup .loaded-username-panel button").click(function() {
		var table_id = $("#select_other_user_table_popup .loaded-username-panel select option:selected").val();
		var table_name = $("#select_other_user_table_popup .loaded-username-panel select option:selected").text();
		
		clear_SelectOtherUserTable_Popup();
		$("#select_other_user_table_popup").hide();
		
		onsubmit("table_list", table_id, table_name);
	});
	
	$("#select_other_user_table_popup").addClass("initialized");
}

function clear_SelectOtherUserTable_Popup() {
	$("#select_other_user_table_popup input").val("");
	$("#select_other_user_table_popup .username-panel").show();
	$("#select_other_user_table_popup .loaded-username-panel").hide();
}

/**
 * Create table + Edit table scripts
 */

function initialize_CreateTablePage() {
	$(".columns_form select.data_type").change(function() {
		onChange_ModifyTable_DataType($(this));
	});
	
	$(".columns_form input[name='column_name']").change(function() {
		onChange_ModifyTable_ColumnName();
	});
	
	$("#add_new_column").click(function() {
		onClick_ModifyTable_AddColumn($(this));
		return false;
	});
	
	$("form .button_panel button").click(function() {
		submit();
		return false;
	});
}

function initialize_EditTablePage() {
	$(".columns_form select.data_type").change(function() {
		onChange_ModifyTable_DataType($(this));
	});
	
	$(".columns_form input[name='column_name']").change(function() {
		onChange_ModifyTable_ColumnName();
	});
	
	$("form .button_panel button[type='submit']").click(function() {
		submit();
		return false;
	});
}

function onClick_ModifyTable_AddColumn(linkObject) {
	var columnObject = $('<li class="input"><label>Column</label><input type="text" name="column_name"/><select class="data_type"><option></option><option value="char">Character</option><option value="number">Number</option><option value="datetime">Date/Time</option><option value="region">Region</option><option value="location">Location</option><option value="builtin">Other data</option><option value="table">Table</option></select><div class="more_inputs"></div><div class="error"></div><div class="clear"></div></li>');
	linkObject.before(columnObject);
	
	columnObject.find("select.data_type").change(function() {
		onChange_ModifyTable_DataType($(this));
	});
	
	columnObject.find("input[name='column_name']").change(function() {
		onChange_ModifyTable_ColumnName();
	});
}

function onChange_ModifyTable_ColumnName() {
	$(".display_column_panel").show();
	
	var old_html = $("#id_display_column_selector").html();
	
	var selectingIndex = document.getElementById("id_display_column_selector").selectedIndex;
	$("#id_display_column_selector").html("");
	
	$(".columns_form input[name='column_name']").each(function() {
		if($(this).val() != "") $("#id_display_column_selector").append("<option>" + $(this).val() + "</option>");
	});
	
	if(old_html != "") document.getElementById("id_display_column_selector").selectedIndex = selectingIndex;
}

function onChange_ModifyTable_DataType(selectObject) {
	var data_type = selectObject.find("option:selected").val();
	
	if(data_type == "datetime") {
		selectObject.parent().find(".more_inputs").html('<select class="related"><option value="datetime">Date and Time</option><option value="date">Date only</option><option value="time">Time only</option></select>');
	
	} else if(data_type == "builtin") {
		selectObject.parent().find(".more_inputs").html('<select class="related"><option></option><option value="thailand_province">Thailand Province</option><option value="thailand_region">Thailand Region</option></select>');
	
	} else if(data_type == "table") {
		selectObject.parent().find(".more_inputs").html('<select class="related"><option></option><option value="mine">My Tables</option><option value="others">User\'s Table</option></select>');
		
		selectObject.parent().find(".more_inputs select.related").change(function() {
			var tableTypeSelectObject = $(this);
			var table_type = $(this).find("option:selected").val();
			
			$(this).parent().find(".related_table").remove();
			
			if(table_type == "mine") {
				$.getJSON("/api/table/list/", function(data) {
					var list_html = '';
					for(var i in data.result) {
						list_html += '<option value="' + data.result[i].id + '">' + data.result[i].name + '</option>';
					}
					
					tableTypeSelectObject.parent().append('<select class="related_table"><option></option>' + list_html + '</select>');
				});
			
			} else if(table_type == "others") {
				var left = $(this).offset().left;
				var top = $(this).offset().top+30;
				
				show_SelectOtherUserTable_Popup(left, top, function(submit_type, table_id, table_name) { // OnSubmit
					onSubmit_ModifyTable_SelectOtherUserTable(tableTypeSelectObject, submit_type, table_id, table_name);
					
				}, function() { // OnClose
					
					// Revert select option to 'blank' if user choose to close without saving
					if(tableTypeSelectObject.parent().find("span.related_table").length == 0) {
						tableTypeSelectObject.find("option:first").attr("selected", "selected");
					}
				});
			}
		});
	
	} else {
		selectObject.parent().find(".more_inputs").html('');
	}
}

function onSubmit_ModifyTable_SelectOtherUserTable(selectObject, submit_type, table_id, table_name) {
	selectObject.parent().find(".related_table").remove();
	
	selectObject.parent().append('<span class="related_table" rel="' + table_id + '">' + table_name + '<a href="#" class="change-user-table">Change</a></span>');
	selectObject.parent().find("a.change-user-table").click(function() {
		var left = selectObject.offset().left;
		var top = selectObject.offset().top+30;
		
		show_SelectOtherUserTable_Popup(left, top, function(submit_type, table_id, table_name) {
			onSubmit_ModifyTable_SelectOtherUserTable(selectObject, submit_type, table_id, table_name);
			
		}, function() {
			// Revert select option to 'blank' if user choose to close without saving
			if(selectObject.parent().find("span.related_table").length == 0) {
				selectObject.find("option:first").attr("selected", "selected");
			}
		});
		
		return false;
	});
}

/**
 * Create query + Edit query scripts
 */

function initialize_CreateQueryPage() {
	$("select.starter_selector").change(function() {
		var selectObject = $(this);
		var table_type = $(this).find("option:selected").val();
		
		if(table_type == "mine") {
			$.getJSON("/api/table/list/", function(data) {
				var list_html = '';
				for(var i in data.result) {
					list_html += '<option value="' + data.result[i].id + '">' + data.result[i].name + '</option>';
				}
				
				selectObject.parent().find(".related_table").remove();
				selectObject.parent().append('<select class="related_table"><option></option>' + list_html + '</select>');
				
				selectObject.parent().find("select.related_table").change(function() {
					load_CreateQueryPage_StarterTable($(this).find("option:selected").val());
				});
			});
		
		} else if(table_type == "others") {
			var left = selectObject.offset().left;
			var top = selectObject.offset().top+30;
			
			show_SelectOtherUserTable_Popup(left, top, function(submit_type, table_id, table_name) {
				onSubmit_ModifyQuery_SelectOtherUserTable(selectObject, submit_type, table_id, table_name);
				
			}, function() { // Revert select option to 'blank' if user choose to close without saving
				if(selectObject.parent().find("span.related_table").length == 0) {
					selectObject.find("option:first").attr("selected", "selected");
				}
			});
			
		} else if(table_type == "builtin") {
			$(this).parent().append('<select class="table_selector"><option></option>{% generate_built_in_table_list %}</select>');
			
			$(this).parent().find("select.table_selector").change(function() {
				load_CreateQueryPage_StarterTable($(this).find("option:selected").val());
			});
		}
	});
	
	$("form button[type='submit']").click(function() {
		submit();
		return false;
	});
}

function load_CreateQueryPage_StarterTable(table_code) {
	$.getJSON("/api/table/?table_code=" + table_code, function(data) {
		if(data.response == "success") {
			$("#starter_panel").html(draw_CreateQueryPage_TableHTML(data.result[0]) + '<div class="manage_filters_popup" style="display:none;"></div>');
			
			$("#starter_panel input.display").click(function() {
				$(this).closest("td").toggleClass("selected");
			});
			
			$("#starter_panel a.manage-filters").click(function() {
				show_ManageQueryFilters_Popup($(this));
				return false;
			});
		}
	});
}

function draw_CreateQueryPage_TableHTML(table_info) {
	var html = '<table rel="' + table_info.id + '"><tr><th>' + table_info.name + '</th></tr><tr><td class="actions"><a href="#" class="manage-filters" title="Filters"><img src="' + MEDIA_URL + '/images/query_filter.png"/>Filters</a> <a href="#" title="Aggregate"><img src="' + MEDIA_URL + '/images/query_aggregate.png"/>Aggregate</a> <a href="#" title="Sort By"><img src="' + MEDIA_URL + '/images/query_sort.png"/>Sort</a></td></tr>';
	var selector = '';
	
	for(var i=0; i<table_info.columns.length; i++) {
		html += '<tr><td rel="' + table_info.columns[i].id + '"><label><input type="checkbox" class="display" /> ' + table_info.columns[i].name + '</label></td></tr>'
		selector += '<option value="' + table_info.columns[i].id + '">' + table_info.columns[i].name + '</option>';
	}
	
	html += '</table><select class="rendered_columns" style="display:none;"><option></option>' + selector + '</select>';
	return html;
}

function onSubmit_ModifyQuery_SelectOtherUserTable(selectObject, submit_type, table_id, table_name) {
	selectObject.parent().find(".related_table").remove();
	
	selectObject.parent().append('<span class="related_table" rel="' + table_id + '">' + table_name + '<a href="#" class="change-user-table">Change</a></span>');
	selectObject.parent().find("a.change-user-table").click(function() {
		var left = selectObject.offset().left;
		var top = selectObject.offset().top+30;
		
		show_SelectOtherUserTable_Popup(left, top, function(submit_type, table_id, table_name) {
			onSubmit_ModifyQuery_SelectOtherUserTable(selectObject, submit_type, table_id, table_name);
			
		}, function() { // Revert select option to 'blank' if user choose to close without saving
			if(selectObject.parent().find("span.related_table").length == 0) {
				selectObject.find("option:first").attr("selected", "selected");
			}
		});
		
		return false;
	});
	
	load_CreateQueryPage_StarterTable(table_id);
}

function show_ManageQueryFilters_Popup(linkObject) {
	var popup_panel = linkObject.closest("div.table_panel").find(".manage_filters_popup");
	if(!popup_panel.hasClass("initialized")) initialize_ManageQueryFilters_Popup(popup_panel);
	popup_panel.show().css({'left':(document.documentElement.clientWidth - popup_panel.width())/2,'top':300});
}

function initialize_ManageQueryFilters_Popup(popup_panel) {
	popup_panel.html('<h4>Filters</h4><div class="select_function_panel"><label><img src="' + MEDIA_URL + '/images/icon_create.png" />Add filter: <select><option></option><option value="equal">Equal</option></select></label></div><ul class="filters"></ul><div class="popup_button_panel"><button>Save and Close</button></div>');
	
	// Close popup
	popup_panel.find(".popup_button_panel button").click(function() {
		popup_panel.hide();
		return false;
	});
	
	// Select function
	popup_panel.find(".select_function_panel select").change(function() {
		var function_name = $(this).find("option:selected").val();
		
		if(function_name != "") {
			var column_html = $(this).closest("div.table_panel").find(".rendered_columns").html();
			var filter_html = "";
			
			if(function_name == "equal") {
				filter_html = '<td class="cell_select_column"><select class="column">' + column_html + '</select></td><td class="cell_text">=</td><td class="cell_parameter"><div><input type="text" name="value"/></div><div><label><input type="checkbox" class="parameter-checkbox"/> Use parameter</label></div></td>';

			} else if(function_name = "[IMPLEMENT OTHER FUNCTIONS HERE]") {
				
			}
			
			var filter_row = $('<li class="filter" rel="' + function_name + '"><table><tr>' + filter_html + '</tr></table><div class="remove_panel"><a href="#" class="remove-filter">Remove</a></div></li>');
			
			$(this).closest(".manage_filters_popup").find("ul.filters").append(filter_row);
			
			filter_row.find(".parameter-checkbox").click(function() {
				if($(this).attr("checked")) {
					$(this).closest(".cell_parameter").find("input[type='text']").attr("disabled", "disabled");
				} else {
					$(this).closest(".cell_parameter").find("input[type='text']").attr("disabled", "");
				}
			});
			
			filter_row.find(".remove-filter").click(function() {
				if(window.confirm("Confirm?")) {
					$(this).closest("li.filter").remove();
				}
				return false;
			});
		}
		
		$(this).find("option:first").attr("selected", true);
	});
	
	popup_panel.addClass("initialized");
}

