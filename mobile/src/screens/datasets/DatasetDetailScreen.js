import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { previewDataset } from '../../api/datasets';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import SectionCard from '../../components/SectionCard';
import { colors } from '../../theme';

export default function DatasetDetailScreen({ route }) {
  const { dataset } = route.params;
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    previewDataset(dataset.id)
      .then(setPreview)
      .catch(() => setError('Failed to load preview.'))
      .finally(() => setLoading(false));
  }, [dataset.id]);

  if (loading) return <LoadingSpinner />;

  const columns = preview?.columns || [];
  // rows come back as arrays (one per row), not dicts
  const rows = preview?.rows || [];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <ErrorMessage message={error} />

      <SectionCard title="Info">
        <View style={styles.row}><Text style={styles.meta}>Rows</Text><Text style={styles.metaVal}>{dataset.row_count}</Text></View>
        <View style={styles.row}><Text style={styles.meta}>Columns</Text><Text style={styles.metaVal}>{dataset.column_count}</Text></View>
        <View style={styles.row}><Text style={styles.meta}>Uploaded</Text><Text style={styles.metaVal}>{new Date(dataset.uploaded_at).toLocaleDateString()}</Text></View>
      </SectionCard>

      <SectionCard title="Columns">
        <View style={styles.chips}>
          {columns.map((col) => (
            <View key={col} style={styles.colChip}>
              <Text style={styles.colText}>{col}</Text>
            </View>
          ))}
        </View>
      </SectionCard>

      {rows.length > 0 && (
        <SectionCard title="Preview (first rows)">
          <ScrollView horizontal>
            <View>
              <View style={styles.tableRow}>
                {columns.map((col) => (
                  <Text key={col} style={[styles.cell, styles.headerCell]} numberOfLines={1}>{col}</Text>
                ))}
              </View>
              {rows.map((row, i) => (
                <View key={i} style={[styles.tableRow, i % 2 === 1 && styles.altRow]}>
                  {row.map((val, j) => (
                    <Text key={j} style={styles.cell} numberOfLines={1}>{val !== null && val !== undefined ? String(val) : ''}</Text>
                  ))}
                </View>
              ))}
            </View>
          </ScrollView>
        </SectionCard>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 5, borderBottomWidth: 1, borderBottomColor: colors.border },
  meta: { fontSize: 14, color: colors.mediumGray },
  metaVal: { fontSize: 14, color: colors.dark, fontWeight: '600' },
  chips: { flexDirection: 'row', flexWrap: 'wrap' },
  colChip: {
    backgroundColor: colors.background,
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 5,
    marginRight: 6,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: colors.border,
  },
  colText: { fontSize: 13, color: colors.dark },
  tableRow: { flexDirection: 'row' },
  altRow: { backgroundColor: colors.background },
  cell: { width: 100, padding: 6, fontSize: 12, color: colors.dark, borderRightWidth: 1, borderRightColor: colors.border },
  headerCell: { fontWeight: '700', color: colors.primary, backgroundColor: '#f8f6ff' },
});
