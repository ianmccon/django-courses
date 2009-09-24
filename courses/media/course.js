var elementlist = elementlist || {};
elementlist.counter = 100;

elementlist.remove_element_from_list = function(list_series, id, element) {
    $(element).parent().remove();
    if( $('ul.elementlist[list_series=' + list_series + '] input[type=hidden]').length == 0) {
        $('ul.elementlist[list_series=' + list_series + '] > li[element_id=-1]').show();
    }
}

elementlist.is_element_in_list = function(list_series, id) {
    return $('ul[list_series=' + list_series + '] input[type=hidden][value=' + id + ']').length != 0
}

function flash_color(element, color) {
    var bg = 'transparent';
    var current = element;
    while(bg == 'transparent') {
        current = current.parent();
        bg = current.css('background-color');
    }
    element.css('background-color',  color)
        .animate( {backgroundColor: bg }, 2000);

}

elementlist.add_element_to_list = function(list_series, element_id, element_display) {
    $('ul.elementlist[list_series=' + list_series + '] > li[element_id=-1]').hide();
    elementlist.counter += 1;

    var html = "";
    html += "<li element_id='" + element_id + "'>";
        html += "<input type='hidden' name='elementlist_" + list_series + "_" + elementlist.counter + "' value='" + element_id + "," + element_display + "'/>" 
        html += element_display
        html += ' <a href="javascript:void(0);" onclick="javascript:elementlist.remove_element_from_list(' + list_series + ', ' + element_id + ', this)">[remove]</a>';
    html += '</li>';
    $('ul.elementlist[list_series=' + list_series + ']').append(html);
    var element = $('ul.elementlist[list_series=' + list_series + '] > li[element_id=' + element_id + ']');
    flash_color(element, '#E6EFC2');
    return length;
}

function course_result(data, list_series) {
    if (!elementlist.is_element_in_list(list_series, data[1])) {
        var length = elementlist.add_element_to_list(list_series, data[1], $('[department_autocomplete="' + list_series + '"]').attr('value') + ' ' + data[0]);
    }
}

function courselist_result(data, list_series) {
    var data = data[1].split(",,");
    elementlist.add_element_to_list(list_series, data[1], data[0]);
    return;
}
