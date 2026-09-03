
    <!-- ALERT 4 -->

    <div style="
      margin-top:28px;
      margin-bottom:12px;
      font-size:18px;
      font-weight:bold;
    ">
      4. Weekly Use-Case Deviation Monitoring
    </div>

    <div style="
      font-size:13px;
      color:#555555;
      margin-bottom:10px;
    ">
      Use cases where latest completed week spend increased
      by more than ${BUDGET_CONFIG.WEEKLY_DEVIATION_THRESHOLD_PCT}%
      compared with the previous week.
    </div>

    ${weeklyDeviationAlerts.length === 0
      ? `
        <div style="
          padding:12px;
          background:#F8F8F8;
        ">
          No weekly use-case deviations above
          ${BUDGET_CONFIG.WEEKLY_DEVIATION_THRESHOLD_PCT}% found.
        </div>
      `
      : `
        <table style="
          width:100%;
          border-collapse:collapse;
          font-size:12px;
        ">
          <thead>
            <tr>
              ${headerCell('Use Case')}
              ${headerCell('VZ VSAD')}
              ${headerCell('VAST ID')}
              ${headerCell('Budget')}
              ${headerCell('Budget Used %')}
              ${headerCell('Previous Week')}
              ${headerCell('Latest Week')}
              ${headerCell('Change $')}
              ${headerCell('Deviation %')}
              ${headerCell('Avg Weekly')}
              ${headerCell('Avg Monthly')}
              ${headerCell('Status')}
            </tr>
          </thead>

          <tbody>
            ${weeklyDeviationAlerts.map(row => `
              <tr>
                <td>${row.vz_usecase || ''}</td>
                <td>${row.vz_vsad || ''}</td>
                <td>${row.vast_id || ''}</td>

                <td>
                  ${row.mapped_budget_usd != null
                    ? formatCurrency(row.mapped_budget_usd)
                    : ''}
                </td>

                <td>
                  ${row.budget_used_pct != null
                    ? Number(row.budget_used_pct).toFixed(2) + '%'
                    : ''}
                </td>

                <td>
                  ${row.previous_week_spend_usd != null
                    ? formatCurrency(row.previous_week_spend_usd)
                    : ''}
                </td>

                <td>
                  ${row.latest_week_spend_usd != null
                    ? formatCurrency(row.latest_week_spend_usd)
                    : ''}
                </td>

                <td>
                  ${row.weekly_change_usd != null
                    ? formatCurrency(row.weekly_change_usd)
                    : ''}
                </td>

                <td>
                  ${row.weekly_deviation_pct != null
                    ? Number(row.weekly_deviation_pct).toFixed(2) + '%'
                    : ''}
                </td>

                <td>
                  ${row.avg_weekly_spend_usd != null
                    ? formatCurrency(row.avg_weekly_spend_usd)
                    : ''}
                </td>

                <td>
                  ${row.avg_monthly_spend_usd != null
                    ? formatCurrency(row.avg_monthly_spend_usd)
                    : ''}
                </td>

                <td>${row.mapping_status || ''}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <p>
          Total weekly deviation records:
          ${weeklyDeviationAlerts.length}
        </p>
      `
    }
