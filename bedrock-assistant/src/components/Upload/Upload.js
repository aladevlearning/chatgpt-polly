import { FileUploader } from '@aws-amplify/ui-react';

const styles = {
    container: { width: 400, margin: '0 auto', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: 20 },
    todo: { marginBottom: 15 },
    input: { border: 'none', backgroundColor: '#ddd', marginBottom: 10, padding: 8, fontSize: 18 },
    todoName: { fontSize: 20, fontWeight: 'bold' },
    todoDescription: { marginBottom: 0 },
    button: { backgroundColor: 'black', color: 'white', outline: 'none', fontSize: 18, padding: '12px 0px' }
  }
  
function Upload() {
   
    return (
        <div style={styles.container}>
            <FileUploader
                acceptedFileTypes={['text/*']}
                accessLevel="private"
            />
        </div>
    );
}
export default Upload; 