function doGet(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var tipo = e.parameter.tipo_registro;

  if (tipo === 'agenda') {
    return ContentService
      .createTextOutput(JSON.stringify(readAgenda(ss)))
      .setMimeType(ContentService.MimeType.JSON);
  }

  if (tipo === 'dados') {
    return ContentService
      .createTextOutput(JSON.stringify(readDados(ss)))
      .setMimeType(ContentService.MimeType.JSON);
  }

  return ContentService
    .createTextOutput(JSON.stringify({ error: 'tipo_registro inválido ou não informado' }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var data = JSON.parse(e.postData.contents);

  if (data.tipo_registro === 'temperatura') {
    var sheet = ss.getSheetByName('temperatura');
    sheet.appendRow([
      data.data_hora,
      data.nome,
      data.local,
      data.area,
      data.temperatura,
      data.status,
    ]);
  }

  if (data.tipo_registro === 'palete') {
    var sheet = ss.getSheetByName('palete');
    sheet.appendRow([
      data.data_hora,
      data.nome,
      data.tipo,
      data.local,
      data.quantidade,
    ]);
  }

  if (data.tipo_registro === 'agenda') {
    var sheet = ss.getSheetByName('agenda');
    sheet.appendRow([
      data.data,
      data.evento,
      data.status || 'Aberto',
      data.observacao || '',
    ]);
  }

  if (data.tipo_registro === 'agenda_status') {
    updateAgendaStatus(ss, data.id, data.status || 'Finalizado');
  }

  return ContentService.createTextOutput('OK');
}

function readAgenda(ss) {
  var sheet = ss.getSheetByName('agenda');
  if (!sheet) {
    return [];
  }

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    return [];
  }

  var displayValues = sheet.getRange(2, 1, lastRow - 1, 4).getDisplayValues();
  var events = [];
  var timeZone = Session.getScriptTimeZone();

  for (var i = 0; i < displayValues.length; i++) {
    var row = displayValues[i];
    var rowIndex = i + 2;
    var dateString = normalizeAgendaDate(row[0], timeZone);

    events.push({
      id: rowIndex,
      data: dateString,
      evento: String(row[1] || ''),
      status: String(row[2] || 'Aberto'),
      observacao: String(row[3] || ''),
    });
  }

  return events;
}

function normalizeAgendaDate(value, timeZone) {
  if (Object.prototype.toString.call(value) === '[object Date]') {
    return Utilities.formatDate(value, timeZone, 'yyyy-MM-dd');
  }

  var text = String(value || '').trim();
  if (!text) {
    return '';
  }

  // Accept dd/mm/yyyy, ddmmyyyy, yyyy-mm-dd, mm/dd/yyyy
  var regex1 = /^(\d{1,2})[\/\-. ](\d{1,2})[\/\-. ](\d{4})$/;
  var regex2 = /^(\d{1,2})[\/\-. ](\d{2})(\d{4})$/;
  var regex3 = /^(\d{4})[\/\-. ](\d{1,2})[\/\-. ](\d{1,2})$/;

  var match = text.match(regex1);
  if (match) {
    var day = parseInt(match[1], 10);
    var month = parseInt(match[2], 10);
    var year = parseInt(match[3], 10);
    return formatDateParts(year, month, day);
  }

  match = text.match(regex2);
  if (match) {
    var day2 = parseInt(match[1], 10);
    var month2 = parseInt(match[2], 10);
    var year2 = parseInt(match[3], 10);
    return formatDateParts(year2, month2, day2);
  }

  match = text.match(regex3);
  if (match) {
    var year3 = parseInt(match[1], 10);
    var month3 = parseInt(match[2], 10);
    var day3 = parseInt(match[3], 10);
    return formatDateParts(year3, month3, day3);
  }

  return text;
}

function formatDateParts(year, month, day) {
  month = month < 10 ? '0' + month : '' + month;
  day = day < 10 ? '0' + day : '' + day;
  return year + '-' + month + '-' + day;
}

function updateAgendaStatus(ss, rowId, status) {
  var sheet = ss.getSheetByName('agenda');
  if (!sheet) {
    return;
  }

  var row = parseInt(rowId, 10);
  if (isNaN(row) || row < 2) {
    return;
  }

  sheet.getRange(row, 3).setValue(status);
}

function readDados(ss) {
  var sheetNames = ['novo_dados', 'dados', 'Dados', 'Novo_dados'];
  var sheet = null;
  
  for (var i = 0; i < sheetNames.length; i++) {
    sheet = ss.getSheetByName(sheetNames[i]);
    if (sheet) {
      break;
    }
  }
  
  if (!sheet) {
    return { error: 'Aba "novo_dados" ou "dados" não encontrada.' };
  }

  var lastRow = sheet.getLastRow();
  var lastCol = sheet.getLastColumn();
  
  if (lastRow < 2) {
    return { error: 'Aba vazia ou sem dados' };
  }

  try {
    var headers = sheet.getRange(1, 1, 1, lastCol).getDisplayValues()[0];
    var values = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();
    var data = [];

    for (var i = 0; i < values.length; i++) {
      var row = values[i];
      var obj = {};
      for (var j = 0; j < headers.length; j++) {
        obj[headers[j]] = row[j];
      }
      data.push(obj);
    }

    return data;
  } catch (error) {
    return { error: 'Erro ao ler aba: ' + error.toString() };
  }
}