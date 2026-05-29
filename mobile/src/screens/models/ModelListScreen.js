import React, { useCallback, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { listModels, deleteModel } from '../../api/models';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import { colors } from '../../theme';

const TYPE_COLOR = { classification: colors.primary, regression: colors.secondary };
const TYPE_LABEL = { classification: 'sınıflandırma', regression: 'regresyon' };

export default function ModelListScreen({ navigation }) {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  async function fetchModels() {
    try {
      const data = await listModels();
      setModels(data);
      setError('');
    } catch {
      setError('Modeller yüklenemedi.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useFocusEffect(useCallback(() => { setLoading(true); fetchModels(); }, []));

  function confirmDelete(model) {
    Alert.alert('Modeli Sil', `"${model.name}" silinsin mi?`, [
      { text: 'İptal', style: 'cancel' },
      {
        text: 'Sil', style: 'destructive',
        onPress: async () => {
          try {
            await deleteModel(model.id);
            setModels((prev) => prev.filter((m) => m.id !== model.id));
          } catch {
            Alert.alert('Hata', 'Model silinemedi.');
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
        data={models}
        keyExtractor={(item) => String(item.id)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchModels(); }} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="hardware-chip-outline" size={48} color={colors.lightGray} />
            <Text style={styles.emptyText}>Henüz model yok</Text>
          </View>
        }
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('ModelDetail', { modelId: item.id })}>
            <View style={styles.cardTop}>
              <Text style={styles.cardTitle} numberOfLines={1}>{item.name}</Text>
              <TouchableOpacity onPress={() => confirmDelete(item)} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Ionicons name="trash-outline" size={18} color={colors.danger} />
              </TouchableOpacity>
            </View>
            <Text style={styles.cardAlgo}>{item.algorithm}</Text>
            <View style={styles.cardFooter}>
              <View style={[styles.typeBadge, { backgroundColor: (TYPE_COLOR[item.model_type] || colors.primary) + '20', borderColor: TYPE_COLOR[item.model_type] || colors.primary }]}>
                <Text style={[styles.typeText, { color: TYPE_COLOR[item.model_type] || colors.primary }]}>{TYPE_LABEL[item.model_type] || item.model_type}</Text>
              </View>
              <Text style={styles.cardDate}>{new Date(item.created_at).toLocaleDateString('tr-TR')}</Text>
            </View>
          </TouchableOpacity>
        )}
      />
      <TouchableOpacity style={styles.fab} onPress={() => navigation.navigate('TrainModel')}>
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
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 15, fontWeight: '700', color: colors.dark, flex: 1 },
  cardAlgo: { fontSize: 13, color: colors.mediumGray, marginTop: 4 },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 10 },
  typeBadge: { borderRadius: 12, borderWidth: 1, paddingHorizontal: 8, paddingVertical: 3 },
  typeText: { fontSize: 11, fontWeight: '600' },
  cardDate: { fontSize: 12, color: colors.lightGray },
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
