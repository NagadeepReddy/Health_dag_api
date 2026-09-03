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

    <div style="
      background:#F8F8F8;
      padding:12px;
      margin-bottom:14px;
      font-size:13px;
    ">
      <strong>Weekly deviations:</strong>
      ${mappedWeeklyDeviations.length}
      <br>
      <strong>Mapping issues:</strong>
      ${weeklyMappingIssues.length}
    </div>


    <!-- ALERT 4A - MAPPED WEEKLY DEVIATIONS -->

    <div style="
      margin-top:18px;
      margin-bottom:10px;
      font-size:15px;
      font-weight:bold;
    ">
      4A. Weekly Use-Case Deviations (&gt;${BUDGET_CONFIG.WEEKLY_DEVIATION_THRESHOLD_PCT}%)
    </div>

    ${mappedWeeklyDeviations.length === 0
      ? `
        <div style="
          padding:12px;
          background:#F8F8F8;
        ">
          No mapped weekly use-case deviations above
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
            </tr>
          </thead>

          <tbody>
            ${mappedWeeklyDeviations.map(row => `
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
              </tr>
            `).join('')}
          </tbody>
        </table>

        <p>
          Total mapped weekly deviations:
          ${mappedWeeklyDeviations.length}
        </p>
      `
    }


    <!-- ALERT 4B - MAPPING ISSUES -->

    <div style="
      margin-top:24px;
      margin-bottom:10px;
      font-size:15px;
      font-weight:bold;
    ">
      4B. Weekly Monitoring Mapping Issues
    </div>

    ${weeklyMappingIssues.length === 0
      ? `
        <div style="
          padding:12px;
          background:#F8F8F8;
        ">
          No weekly monitoring mapping issues found.
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
              ${headerCell('Previous Week')}
              ${headerCell('Latest Week')}
              ${headerCell('Change $')}
              ${headerCell('Deviation %')}
              ${headerCell('Mapping Status')}
            </tr>
          </thead>

          <tbody>
            ${weeklyMappingIssues.map(row => `
              <tr>
                <td>${row.vz_usecase || ''}</td>
                <td>${row.vz_vsad || ''}</td>
                <td>${row.vast_id || ''}</td>

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

                <td>${row.mapping_status || ''}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <p>
          Total weekly monitoring mapping issues:
          ${weeklyMappingIssues.length}
        </p>
      `
    }
