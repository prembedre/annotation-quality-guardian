import React from 'react';
import { ScoreIndicator } from './ScoreIndicator';
import { FlagStatusBadge } from './FlagStatusBadge';
import { LoadingState, EmptyState } from './States';

/**
 * ReviewQueueTable component displays the review queue data in a professional table
 */
export function ReviewQueueTable({ items, loading }) {
  if (loading) {
    return <LoadingState />;
  }

  if (!items || items.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Item ID</th>
            <th>Annotation</th>
            <th>Annotator</th>
            <th>Quality / Trust Score</th>
            <th>Flag Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const annotation = item.annotations && item.annotations.length > 0 ? item.annotations[0] : null;
            return (
              <tr key={item.item_id}>
                <td>
                  <strong>{item.external_id || item.item_id}</strong>
                </td>
                <td className="annotation-cell">
                  <span title={annotation ? annotation.label : 'No annotation'}>
                    {annotation ? annotation.label : 'No annotation'}
                  </span>
                </td>
                <td>{annotation ? annotation.annotator_name : 'Unknown'}</td>
                <td>
                  <ScoreIndicator
                    trustScore={item.trust_score != null ? item.trust_score * 100 : null}
                  />
                </td>
                <td>
                  <FlagStatusBadge isFlagged={item.flagged} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
