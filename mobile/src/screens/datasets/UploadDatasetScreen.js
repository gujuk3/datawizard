import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { Ionicons } from '@expo/vector-icons';
import { uploadDataset } from '../../api/datasets';
import ErrorMessage from '../../components/ErrorMessage';
import SectionCard from '../../components/SectionCard';
import { colors } from '../../theme';

export default function UploadDatasetScreen({ navigation }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  async function pickFile() {
    const picked = await DocumentPicker.getDocumentAsync({ type: ['text/csv', 'text/comma-separated-values', '*/*'] });
    if (!picked.canceled && picked.assets?.length) {
      setFile(picked.assets[0]);
      setError('');
      setResult(null);
    }
  }

  async function handleUpload() {
    if (!file) { setError('Lütfen bir CSV dosyası seçin.'); return; }
    setLoading(true);
    setError('');
    try {
      const data = await uploadDataset(file.uri, file.name, file.mimeType || 'text/csv');
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.error || 'Yükleme başarısız. Lütfen tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  }

  if (result) {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <View style={styles.successHeader}>
          <Ionicons name="checkmark-circle" size={48} color={colors.secondary} />
          <Text style={styles.successTitle}>Yükleme başarılı</Text>
          <Text style={styles.successSub}>{result.dataset?.name}</Text>
        </View>

        {result.initial_insights ? (
          <SectionCard title="AI İçgörüleri">
            <Text style={styles.insights}>{result.initial_insights}</Text>
          </SectionCard>
        ) : null}

        <TouchableOpacity
          style={styles.button}
          onPress={() => navigation.replace('DatasetDetail', { dataset: result.dataset })}
        >
          <Text style={styles.buttonText}>Veri Setini Görüntüle</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.secondaryBtn} onPress={() => navigation.goBack()}>
          <Text style={styles.secondaryBtnText}>Veri Setlerine Dön</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  return (
    <View style={styles.container}>
      <ErrorMessage message={error} />

      <TouchableOpacity style={styles.dropZone} onPress={pickFile}>
        <Ionicons name={file ? 'document-text' : 'cloud-upload-outline'} size={48} color={file ? colors.secondary : colors.lightGray} />
        <Text style={styles.dropText}>
          {file ? file.name : 'CSV dosyası seçmek için dokunun'}
        </Text>
        {file && <Text style={styles.dropMeta}>{(file.size / 1024).toFixed(1)} KB</Text>}
      </TouchableOpacity>

      {file && (
        <TouchableOpacity style={styles.changeBtn} onPress={pickFile}>
          <Text style={styles.changeBtnText}>Dosya değiştir</Text>
        </TouchableOpacity>
      )}

      <TouchableOpacity
        style={[styles.button, !file && styles.buttonDisabled]}
        onPress={handleUpload}
        disabled={!file || loading}
      >
        <Text style={styles.buttonText}>{loading ? 'Yükleniyor…' : 'Veri Seti Yükle'}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 20, paddingBottom: 40 },
  dropZone: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: colors.border,
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
    marginVertical: 20,
    marginHorizontal: 20,
  },
  dropText: { fontSize: 15, color: colors.mediumGray, marginTop: 12, textAlign: 'center' },
  dropMeta: { fontSize: 12, color: colors.lightGray, marginTop: 4 },
  changeBtn: { alignSelf: 'center', marginBottom: 8 },
  changeBtnText: { color: colors.primary, fontSize: 14 },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
    marginTop: 8,
    marginHorizontal: 20,
  },
  buttonDisabled: { backgroundColor: colors.lightGray },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  successHeader: { alignItems: 'center', marginBottom: 20 },
  successTitle: { fontSize: 22, fontWeight: '700', color: colors.dark, marginTop: 12 },
  successSub: { fontSize: 14, color: colors.mediumGray, marginTop: 4 },
  insights: { fontSize: 15, color: colors.dark, lineHeight: 24 },
  secondaryBtn: { padding: 15, alignItems: 'center', marginTop: 4 },
  secondaryBtnText: { color: colors.mediumGray, fontSize: 15 },
});
