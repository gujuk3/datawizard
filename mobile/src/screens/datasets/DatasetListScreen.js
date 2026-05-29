import React, { useCallback, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { listDatasets, deleteDataset } from '../../api/datasets';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import { colors } from '../../theme';

export default function DatasetListScreen({ navigation }) {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  async function fetchDatasets() {
    try {
      const data = await listDatasets();
      setDatasets(data);
      setError('');
    } catch {
      setError('Veri setleri yüklenemedi.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useFocusEffect(useCallback(() => { setLoading(true); fetchDatasets(); }, []));

  function confirmDelete(dataset) {
    Alert.alert('Veri Setini Sil', `"${dataset.name}" silinsin mi?`, [
      { text: 'İptal', style: 'cancel' },
      {
        text: 'Sil', style: 'destructive',
        onPress: async () => {
          try {
            await deleteDataset(dataset.id);
            setDatasets((prev) => prev.filter((d) => d.id !== dataset.id));
          } catch {
            Alert.alert('Hata', 'Veri seti silinemedi.');
          }
        },
      },
    ]);
  }

  if (loading) return <LoadingSpinner />;

  return (
    <View style={styles.container}>
      <ErrorMessage message={error} />
      <FlatList
        data={datasets}
        keyExtractor={(item) => String(item.id)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchDatasets(); }} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="folder-open-outline" size={48} color={colors.lightGray} />
            <Text style={styles.emptyText}>Henüz veri seti yok</Text>
          </View>
        }
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('DatasetDetail', { dataset: item })}>
            <View style={styles.cardLeft}>
              <Ionicons name="document-text-outline" size={22} color={colors.primary} />
              <View style={styles.cardInfo}>
                <Text style={styles.cardTitle} numberOfLines={1}>{item.name}</Text>
                <Text style={styles.cardMeta}>{item.row_count} satır · {item.column_count} sütun</Text>
              </View>
            </View>
            <TouchableOpacity onPress={() => confirmDelete(item)} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
              <Ionicons name="trash-outline" size={20} color={colors.danger} />
            </TouchableOpacity>
          </TouchableOpacity>
        )}
      />
      <TouchableOpacity style={styles.fab} onPress={() => navigation.navigate('UploadDataset')}>
        <Ionicons name="add" size={28} color="#fff" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: 12 },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  cardLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  cardInfo: { marginLeft: 12, flex: 1 },
  cardTitle: { fontSize: 15, fontWeight: '600', color: colors.dark },
  cardMeta: { fontSize: 12, color: colors.mediumGray, marginTop: 2 },
  empty: { alignItems: 'center', marginTop: 80 },
  emptyText: { color: colors.lightGray, fontSize: 15, marginTop: 12 },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 4,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 6,
  },
});
