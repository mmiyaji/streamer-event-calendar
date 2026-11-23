function formatEventDates({start, end, allDay}) {
  if (!start) return '未定';
  if (!allDay) {
    const from = start.toLocaleString('ja-JP');
    return end ? from + ' ～ ' + end.toLocaleString('ja-JP') : from;
  }
  const from = start.toLocaleDateString('ja-JP');
  if (!end) return from;
  // FullCalendar supplies the first day after the event in local calendar time.
  const lastDay = new Date(end.getTime());
  lastDay.setDate(lastDay.getDate() - 1);
  const through = lastDay.toLocaleDateString('ja-JP');
  return from === through ? from : from + ' ～ ' + through;
}

function detail({event}) {
  const props = event.extendedProps;
  const body = document.querySelector('#detail-body');
  document.querySelector('#detail-title').textContent = event.title;
  body.replaceChildren();
  function addRow(label, value) {
    if (!value) return;
    const row = document.createElement('div');
    row.className = 'detail-row';
    const heading = document.createElement('strong');
    heading.textContent = label;
    row.append(heading, ' ' + value);
    body.append(row);
  }
  addRow('日時:', formatEventDates(event));
  addRow('出演:', props.persons?.join('、'));
  addRow('場所:', props.location);
  addRow('補足:', props.notes);

  if (props.url) {
    let url;
    try {
      url = new URL(props.url);
    } catch {
      // Events with an invalid source URL still have usable details.
    }
    if (url?.protocol === 'https:') {
      const link = document.createElement('a');
      link.className = 'button';
      link.href = url.href;
      link.target = '_blank';
      link.rel = 'noopener';
      link.textContent = '情報元を開く';
      body.append(link);
    }
  }
  document.querySelector('#detail').showModal();
}
