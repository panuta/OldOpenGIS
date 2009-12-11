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

function onChange_ModifyTable_ColumnName(selectObject) {
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
			var select_object = $(this);
			var table_type = $(this).find("option:selected").val();
			
			$(this).parent().find(".related_table").remove();
			
			if(table_type == "mine") {
				$.getJSON("/api/table/list/", function(data) {
					var list_html = '';
					for(var i in data.result) {
						list_html += '<option value="' + data.result[i].id + '">' + data.result[i].name + '</option>';
					}
					
					select_object.parent().append('<select class="related_table"><option></option>' + list_html + '</select>');
				});
			
			} else if(table_type == "others") {
				var left = selectObject.offset().left;
				var top = selectObject.offset().top+30;
				
				// $("#select_other_user_table_popup").show().css({'left':selectObject.offset().left,'top':selectObject.offset().top+30});
				
				show_construct_table_select_other_user_table_popup($(this));
			}
		});
	
	} else {
		selectObject.parent().find(".more_inputs").html('');
	}
}

var activeOtherUserTableSelector = null;

function show_SelectOtherUserTable_Popup(left, top, onsubmit, onclose) {
	if(!$("select_other_user_table_popup").hasClass("initialized")) initialize_SelectOtherUserTable_Popup(onsubmit, onclose);
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
}

function clear_SelectOtherUserTable_Popup() {
	$("#select_other_user_table_popup input").val("");
	$("#select_other_user_table_popup .username-panel").show();
	$("#select_other_user_table_popup .loaded-username-panel").hide();
}








function show_construct_table_select_other_user_table_popup(selectObject) {
	if(activeOtherUserTableSelector == null) initialize_construct_table_select_other_user_table_popup();
	activeOtherUserTableSelector = selectObject;
	
	$("#select_other_user_table_popup").show().css({'left':selectObject.offset().left,'top':selectObject.offset().top+30});
}

function initialize_construct_table_select_other_user_table_popup() {
	$("#select_other_user_table_popup").html('<div class="close_panel"><a href="#">Close</a></div>' +
		'<h4>Choose table</h4>' + 
		'<div class="panel code-panel"><label for="id_table_code">from Table Code:</label><div class="right_panel"><input type="text" id="id_table_code" name="table_code"/> <button>Use this code</button></div></div>' + 
		'<div class="panel">or</div>' + 
		'<div class="panel username-panel"><label for="id_table_username">from Username:</label><div class="right_panel"><input type="text" id="id_table_username" name="table_username"/> <button class="load-user-tables">Load</button></div></div>' + 
		'<div class="panel loaded-username-panel" style="display:none;"><label for="id_table_username">from Username:</label><div class="right_panel"><span class="username"></span> <a href="#">Change</a><div class="tables_panel"><select name="table_list"></select><button>Use this table</button></div></div></div>');
	
	// Close popup
	$("#select_other_user_table_popup .close_panel a").click(function() {
		clear_construct_table_select_other_user_table_popup();
		$("#select_other_user_table_popup").hide();
		
		// Revert select option to 'blank' if user choose to close without saving
		if(activeOtherUserTableSelector.parent().find("span.related_table").length == 0) {
			activeOtherUserTableSelector.find("option:first").attr("selected", "selected");
		}
		return false;
	});
	
	// Select table from code
	$("#select_other_user_table_popup .code-panel button").click(function() {
		// TODO
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
		activeOtherUserTableSelector.parent().find(".related_table").remove();
		
		var table_id = $("#select_other_user_table_popup .loaded-username-panel select option:selected").val();
		var table_name = $("#select_other_user_table_popup .loaded-username-panel select option:selected").text();
		
		activeOtherUserTableSelector.parent().append('<span class="related_table" rel="' + table_id + '">' + table_name + '<a href="#" class="change-user-table">Change</a></span>');
		activeOtherUserTableSelector.parent().find("a.change-user-table").click(function() {
			show_construct_table_select_other_user_table_popup($(this).parent().find("select.related"));
			return false;
		});
		
		clear_construct_table_select_other_user_table_popup();
		$("#select_other_user_table_popup").hide();
	});
}

function clear_construct_table_select_other_user_table_popup() {
	$("#select_other_user_table_popup input").val("");
	
	$("#select_other_user_table_popup .username-panel").show();
	$("#select_other_user_table_popup .loaded-username-panel").hide();
}


/**
 * Create query + Edit query scripts
 */

var activeManageQueryFilterLink = null;

function show_construct_query_manage_filters_popup(linkObject) {
	var popup_panel = linkObject.closest("div.table_panel").find(".manage_filters_popup");
	
	if(activeManageQueryFilterLink == null) initialize_show_construct_query_manage_filters_popup(popup_panel);
	activeManageQueryFilterLink = linkObject;
	
	//popup_panel.show().css({'left':(document.documentElement.clientWidth - popup_panel.width())/2,'top':(document.documentElement.clientHeight - $("#manage_query_filter_popup").height())/2});
	popup_panel.show().css({'left':(document.documentElement.clientWidth - popup_panel.width())/2,'top':300});
}

function initialize_show_construct_query_manage_filters_popup(popup_panel) {
	popup_panel.html('<h4>Filters</h4><ul class="filters"><li><a href="#" class="add-filter">Add new filter</a></li></ul><div class="popup_button_panel"><button>Save</button></div>');
	
	// Close popup
	popup_panel.find(".popup_button_panel button").click(function() {
		popup_panel.hide();
		return false;
	});
	
	// Add new row
	popup_panel.find(".add-filter").click(function() {
		var new_row = $('<li class="filter"><span class="function"><a href="#" class="remove-filter">Remove</a><select><option></option><option value="equal">Equal</option></select></span><span class="criteria"></span></li>');
		
		new_row.find(".function select").change(function() {
			var function_name = $(this).find("option:selected").val();
			var column_html = $(this).closest("div.table_panel").find(".rendered_columns").html();
			
			if(function_name == "equal") {
				$(this).closest("li.filter").find(".criteria").html('<select class="column">' + column_html + '</select> = <input type="text" name="value"/> <label><input type="checkbox" class="parameter-checkbox"/> Use parameter</label>');
				
				$(this).closest("li.filter").find(".parameter-checkbox").click(function() {
					if($(this).attr("checked")) {
						$(this).parent().parent().find("input[type='text']").attr("disabled", "disabled");
					} else {
						$(this).parent().parent().find("input[type='text']").attr("disabled", "");
					}
				});
			}
		});
		
		new_row.find(".remove-filter").click(function() {
			if(window.confirm("Confirm?")) {
				$(this).closest("li.filter").remove();
			}
			return false;
		});
		
		$(this).before(new_row);
		
		return false;
	});
}
