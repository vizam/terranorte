function editarPropietario(evt) {
    if ( ! window.confirm('Quiere editar este registro ?') ) {
        return false;
    }
    elementos = document.querySelectorAll("input:not([id='tasa_dia']");
    document.querySelector("fieldset").disabled = false
    for (elemento of elementos) {
        elemento.value = evt.target.dataset[elemento.name];
    }
    document.querySelector("form[id='editar_propietario'").action = `/propietarios/editar/${evt.target.dataset['edificio']}/${evt.target.dataset['apartamento']}`;
    window.scrollTo(0,0)
}


//
//Populate Form for Recibo Editing
//
function editarRecibo(evt) {
    if ( ! window.confirm('Quiere editar ese registro ?') ) {
        return false;
    }
    document.querySelector("fieldset[form='editar_recibo'").disabled = false;
    elementos = document.querySelectorAll("input");
    for (elemento of elementos) {
        if (elemento.id == "tasa_dia") {
            continue;
        }
        elemento.value = evt.target.dataset[elemento.name]
    }
    for (elemento of elementos) {
        if (elemento.name == 'tasa_dia') {
            continue;
        }
        if (elemento.name == 'concepto') {
            break;
        } 
        elemento.setAttribute('readonly', 'readonly');
    }
    window.scrollTo(0,0)
}

function deletePrevent(evt) {
    if ( ! window.confirm("Desea borrar el registro ?") ) {
        evt.preventDefault()

    }
}

function generarPrevent(evt) {
    if ( ! window.confirm("Desea generar todos estos recibos ?") ) {
        evt.preventDefault()

    }
}

function deleteMesPrevent(evt) {
    if ( ! window.confirm("Desea eliminar todos los recibos del mes ?") ) {
        evt.preventDefault()
    }
}

function cerrarMesPrevent(evt) {
    if ( ! window.confirm("Desea cerrar los gastos del mes ?") ) {
        evt.preventDefault()
    }
}

// function editarRecibo(evt) {

//     rowId = evt.target.dataset['rowid']
//     fila = document.querySelector("tr[data-rowid='" + rowId + "']")
//     console.log(fila)
//     longitud = fila.children.length
//     console.log(longitud)



//     for (x = 0; x < longitud; x++) {
//         console.log(fila.children[x].innerHTML)

//     };
// }

function aplicarPago(evt) {
    console.log(evt.target.dataset['rowid'])
}



function guardarTasa() {
    tasa = document.querySelector("input[id='tasa_dia']").value;
    localStorage.setItem('tasa', tasa);
}