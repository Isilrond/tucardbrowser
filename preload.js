const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  imageBase: 'tu-img://',
  loadData: (callback) => {
    ipcRenderer.on('load-progress', (event, progress) => {
      callback(progress, null)
    })
    ipcRenderer.invoke('load-data').then(rawJson => {
      callback(100, rawJson)
    })
  }
})
