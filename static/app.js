document.addEventListener('DOMContentLoaded', () => {
  const dateInput = document.getElementById('issueDate');
  if (dateInput) {
    dateInput.value = new Date().toISOString().split('T')[0];
  }

  const loadSampleBtn = document.getElementById('loadSampleBtn');
  const recipientsInput = document.getElementById('recipientsInput');
  if (loadSampleBtn && recipientsInput) {
    loadSampleBtn.addEventListener('click', () => {
      recipientsInput.value = [
        'Alexander Wright, alexander@example.com',
        'Sophia Martinez, sophia@example.com',
        'Ethan Johnson, ethan@example.com',
        'Olivia Chen, olivia@example.com',
        'Liam Patel, liam@example.com'
      ].join('\n');
    });
  }

  const csvDropZone = document.getElementById('csvDropZone');
  const csvFileInput = document.getElementById('csvFileInput');
  const dropZoneText = document.getElementById('dropZoneText');

  if (csvDropZone && csvFileInput && recipientsInput) {
    csvDropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      csvDropZone.style.borderColor = 'var(--apple-blue)';
    });

    csvDropZone.addEventListener('dragleave', () => {
      csvDropZone.style.borderColor = 'rgba(255, 255, 255, 0.18)';
    });

    csvDropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      csvDropZone.style.borderColor = 'rgba(255, 255, 255, 0.18)';
      if (e.dataTransfer.files.length) {
        handleCsvFile(e.dataTransfer.files[0]);
      }
    });

    csvFileInput.addEventListener('change', (e) => {
      if (e.target.files.length) {
        handleCsvFile(e.target.files[0]);
      }
    });
  }

  function handleCsvFile(file) {
    if (dropZoneText) {
      dropZoneText.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      const lines = event.target.result.split(/\r?\n/).filter(l => l.trim().length > 0);
      recipientsInput.value = lines.join('\n');
    };
    reader.readAsText(file);
  }

  const jobForm = document.getElementById('jobForm');
  const submitBtn = document.getElementById('submitBtn');
  const placeholder = document.getElementById('jobPlaceholder');
  const progressSection = document.getElementById('jobProgressSection');
  const displayJobId = document.getElementById('displayJobId');
  const displayStatus = document.getElementById('displayStatus');
  const statProcessed = document.getElementById('statProcessed');
  const statSuccess = document.getElementById('statSuccess');
  const statFailed = document.getElementById('statFailed');
  const progressBar = document.getElementById('progressBar');
  const downloadZipBtn = document.getElementById('downloadZipBtn');
  const tableBody = document.getElementById('certificatesTableBody');

  let pollInterval = null;

  if (jobForm) {
    jobForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const rawText = recipientsInput.value.trim();
      const lines = rawText.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
      const recipients = [];

      for (const line of lines) {
        const parts = line.split(',');
        const name = parts[0] ? parts[0].trim() : '';
        const email = parts[1] ? parts[1].trim() : null;
        if (name && name.toLowerCase() !== 'name') {
          recipients.push({ name, email });
        }
      }

      if (recipients.length === 0) {
        alert('Please provide at least one valid recipient name.');
        return;
      }

      const payload = {
        event_name: document.getElementById('eventName').value.trim(),
        issuer_name: document.getElementById('issuerName').value.trim(),
        issue_date: document.getElementById('issueDate').value.trim(),
        recipients
      };

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>Processing Generation...</span>';

      let useClientFallback = false;

      try {
        const res = await fetch('/api/jobs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const job = await res.json();
          placeholder.classList.add('hidden');
          progressSection.classList.remove('hidden');
          startPollingJob(job.id);
        } else {
          useClientFallback = true;
        }
      } catch {
        useClientFallback = true;
      }

      if (useClientFallback) {
        placeholder.classList.add('hidden');
        progressSection.classList.remove('hidden');
        processClientSide(payload);
      }
    });
  }

  function startPollingJob(jobId) {
    if (pollInterval) clearInterval(pollInterval);

    displayJobId.textContent = jobId.slice(0, 8).toUpperCase();
    downloadZipBtn.classList.add('hidden');

    const poll = async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        if (!res.ok) return;
        const job = await res.json();

        displayStatus.textContent = job.status;
        displayStatus.className = `status-badge ${job.status}`;
        if (statProcessed) statProcessed.textContent = `${job.processed_count} / ${job.total_count}`;
        if (statSuccess) statSuccess.textContent = `${job.success_count}`;
        if (statFailed) statFailed.textContent = `${job.failure_count}`;

        const pct = job.total_count > 0 ? (job.processed_count / job.total_count) * 100 : 0;
        progressBar.style.width = `${pct}%`;

        renderTable(job.certificates);

        if (job.status === 'completed' || job.status === 'failed') {
          clearInterval(pollInterval);
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Generate Certificates</span>';

          if (job.success_count > 0) {
            downloadZipBtn.href = `/api/jobs/${job.id}/download`;
            downloadZipBtn.classList.remove('hidden');
          }
        }
      } catch (err) {
        console.error(err);
      }
    };

    poll();
    pollInterval = setInterval(poll, 700);
  }

  async function processClientSide(payload) {
    const jobId = 'CLIENT-' + Math.random().toString(36).substring(2, 9).toUpperCase();
    displayJobId.textContent = jobId;
    displayStatus.textContent = 'processing';
    displayStatus.className = 'status-badge processing';

    const total = payload.recipients.length;
    let processed = 0;
    let success = 0;
    const certResults = [];

    const zip = window.JSZip ? new window.JSZip() : null;

    for (const r of payload.recipients) {
      await new Promise(res => setTimeout(res, 250));

      const certId = 'CERT-' + Math.random().toString(36).substring(2, 8).toUpperCase();
      let pdfBlobUrl = null;
      let pdfBytes = null;

      if (window.jspdf && window.jspdf.jsPDF) {
        const doc = new window.jspdf.jsPDF({ orientation: 'landscape', format: 'a4' });
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();

        doc.setFillColor(248, 250, 252);
        doc.rect(0, 0, pageWidth, pageHeight, 'F');

        doc.setDrawColor(15, 23, 42);
        doc.setLineWidth(1.5);
        doc.rect(8, 8, pageWidth - 16, pageHeight - 16);

        doc.setDrawColor(217, 119, 6);
        doc.setLineWidth(0.8);
        doc.rect(11, 11, pageWidth - 22, pageHeight - 22);

        doc.setFont('times', 'bold');
        doc.setFontSize(26);
        doc.setTextColor(15, 23, 42);
        doc.text('CERTIFICATE OF ACHIEVEMENT', pageWidth / 2, 45, { align: 'center' });

        doc.setDrawColor(217, 119, 6);
        doc.setLineWidth(0.5);
        doc.line(pageWidth / 2 - 50, 50, pageWidth / 2 + 50, 50);

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11);
        doc.setTextColor(180, 83, 9);
        doc.text('THIS IS PROUDLY PRESENTED TO', pageWidth / 2, 62, { align: 'center' });

        doc.setFont('times', 'bold');
        doc.setFontSize(30);
        doc.setTextColor(30, 58, 138);
        doc.text(r.name, pageWidth / 2, 85, { align: 'center' });

        doc.setFont('helvetica', 'italic');
        doc.setFontSize(12);
        doc.setTextColor(71, 85, 105);
        doc.text('For outstanding performance and successful completion of', pageWidth / 2, 102, { align: 'center' });

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(18);
        doc.setTextColor(15, 23, 42);
        doc.text(payload.event_name, pageWidth / 2, 118, { align: 'center' });

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11);
        doc.text(payload.issue_date, 55, 155, { align: 'center' });
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.setTextColor(100, 116, 139);
        doc.text('DATE ISSUED', 55, 162, { align: 'center' });

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11);
        doc.setTextColor(15, 23, 42);
        doc.text(payload.issuer_name, pageWidth - 55, 155, { align: 'center' });
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.setTextColor(100, 116, 139);
        doc.text('AUTHORIZED SIGNATORY', pageWidth - 55, 162, { align: 'center' });

        doc.setFontSize(8);
        doc.text('Certificate ID: ' + certId, pageWidth / 2, 185, { align: 'center' });

        pdfBytes = doc.output('blob');
        pdfBlobUrl = URL.createObjectURL(pdfBytes);

        if (zip) {
          const safeName = r.name.replace(/[^a-zA-Z0-9_-]/g, '_');
          zip.file(`${safeName}_${certId}.pdf`, pdfBytes);
        }
      }

      processed++;
      success++;

      certResults.push({
        id: certId,
        recipient_name: r.name,
        recipient_email: r.email,
        status: 'success',
        download_url: pdfBlobUrl
      });

      if (statProcessed) statProcessed.textContent = `${processed} / ${total}`;
      if (statSuccess) statSuccess.textContent = `${success}`;
      if (statFailed) statFailed.textContent = '0';
      const pct = (processed / total) * 100;
      progressBar.style.width = `${pct}%`;

      renderTable(certResults);
    }

    displayStatus.textContent = 'completed';
    displayStatus.className = 'status-badge completed';
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<span>Generate Certificates</span>';

    if (zip && success > 0) {
      zip.generateAsync({ type: 'blob' }).then(blob => {
        downloadZipBtn.href = URL.createObjectURL(blob);
        downloadZipBtn.download = `${payload.event_name.replace(/[^a-zA-Z0-9_-]/g, '_')}_certificates.zip`;
        downloadZipBtn.classList.remove('hidden');
      });
    }
  }

  function renderTable(certificates) {
    if (!certificates || !tableBody) return;
    tableBody.innerHTML = '';

    for (const cert of certificates) {
      const tr = document.createElement('tr');
      const actionHtml = cert.status === 'success' && cert.download_url
        ? `<a href="${cert.download_url}" target="_blank" download="${cert.recipient_name}_certificate.pdf" class="cert-btn-link">Download PDF</a>`
        : `<span style="color: var(--apple-red); font-size: 11px;">${cert.error_message || 'Failed'}</span>`;

      tr.innerHTML = `
        <td>
          <div style="font-weight: 600; color: #fff;">${cert.recipient_name}</div>
          <div style="font-size: 11px; color: var(--text-tertiary);">${cert.recipient_email || 'No email provided'}</div>
        </td>
        <td><span class="status-badge ${cert.status}">${cert.status}</span></td>
        <td>${actionHtml}</td>
      `;
      tableBody.appendChild(tr);
    }
  }

  fetch('/api/health')
    .then(r => r.json())
    .then(data => {
      const statusText = document.getElementById('apiStatusText');
      if (statusText && data.status === 'healthy') {
        statusText.textContent = 'Engine Ready';
      }
    })
    .catch(() => {
      const statusText = document.getElementById('apiStatusText');
      if (statusText) statusText.textContent = 'Engine Ready (Client)';
    });
});
